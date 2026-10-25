import uuid
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Request,Agency,ClassificationResult,RequestEvent,User,RequestWorkflow,utcnow
from backend.app.audit.service import record
from backend.app.ml.classifier import Classifier,ModelUnavailable
from backend.app.requests.schemas import RequestCreate
from backend.app.workflow.routing import resolve_route
from backend.app.models import ServiceFormVersion,ServiceForm
from backend.app.forms.service import resolve_submission_form


def scoped_query(actor: User):
    query=select(Request)
    if actor.role=='citizen':
        return query.where(Request.citizen_id==actor.id)
    if actor.role=='staff':
        return query.where(select(RequestWorkflow.id).where(RequestWorkflow.request_id==Request.id,RequestWorkflow.agency_id==actor.agency_id).exists()) if actor.agency_id else query.where(False)
    if actor.role=='admin':
        return query
    return query.where(False)


def get_request(session: Session,actor: User,request_id: int) -> Request:
    request=session.scalar(scoped_query(actor).where(Request.id==request_id))
    if request is None:
        raise HTTPException(404,'Permohonan tidak ditemukan.')
    return request


def submit_request(session: Session,actor: User,payload: RequestCreate,classifier: Classifier|None) -> Request:
    if classifier is None:
        raise HTTPException(503,'Model belum tersedia. Administrator perlu menjalankan training.')
    try:
        prediction=classifier.predict(payload.title+' '+payload.description)
    except ModelUnavailable:
        raise HTTPException(503,'Model belum tersedia.')
    # Hold the current agency state until the routing transaction commits.
    route=resolve_route(session,prediction.agency_code)
    agency=route[0] if route else None
    form_version=resolve_submission_form(session,payload.form_version_id,payload.form_answers) if payload.form_version_id is not None else None
    form_agency=session.get(Agency,session.get(ServiceForm,form_version.form_id).agency_id) if form_version else None
    mismatch=bool(form_agency and form_agency.code!=prediction.agency_code)
    review=not prediction.auto_routing_enabled or prediction.confidence<prediction.threshold or not prediction.known_features or not route
    review=review or mismatch
    item=Request(reference='SGWA-'+uuid.uuid4().hex[:16].upper(),citizen_id=actor.id,title=payload.title,description=payload.description,assigned_agency_id=None if review else agency.id,status='escalated' if review else 'pending')
    session.add(item);session.flush()
    if form_version:
        item.form_version_id=form_version.id;item.form_answers=payload.form_answers
    all_att_ids = list(payload.attachment_ids)
    if payload.form_answers:
        for val in payload.form_answers.values():
            if isinstance(val, int):
                all_att_ids.append(val)
            elif isinstance(val, dict) and ('id' in val or 'attachment_id' in val):
                all_att_ids.append(val.get('id') or val.get('attachment_id'))
    if all_att_ids:
        from backend.app.attachments.service import link_attachments_to_request
        link_attachments_to_request(session, actor, item.id, all_att_ids, default_agency_id=form_agency.id if form_agency else (agency.id if agency else None))
    if not review:
        now=utcnow()
        session.add_all([RequestWorkflow(request_id=item.id,agency_id=a.id,due_at=now+timedelta(days=a.sla_days)) for a in route])
    session.add(ClassificationResult(request_id=item.id,predicted_agency_code=prediction.agency_code,probabilities=prediction.probabilities,confidence=prediction.confidence,needs_review=review,model_version=prediction.model_version))
    session.add(RequestEvent(request_id=item.id,actor_id=actor.id,event_type='submitted',from_status=None,to_status=item.status,note='Instansi formulir berbeda dari prediksi ML. Perlu pemeriksaan manual.' if mismatch else 'Perlu pemeriksaan manual.' if review else 'Diteruskan berdasarkan klasifikasi ML.'))
    record(session,actor.id,'request.submitted','request',item.id,{'status':item.status,'assigned_agency_id':item.assigned_agency_id})
    from backend.app.notifications.service import notify_request_event
    notify_request_event(session,item,f'request:{item.id}:1:submitted','submitted',[a.id for a in route] if not review else [])
    session.commit()
    return item


def iso(value):
    return value.isoformat()+'Z' if value else None


def serialize(session: Session,item: Request,detail=False,*,actor:User|None=None):
    agency=session.get(Agency,item.assigned_agency_id) if item.assigned_agency_id else None
    data={'id':item.id,'reference':item.reference,'citizen_id':item.citizen_id,'title':item.title,'description':item.description,'assigned_agency_id':item.assigned_agency_id,'agency_name':agency.name if agency else None,'status':item.status,'version':item.version,'created_at':iso(item.created_at),'updated_at':iso(item.updated_at)}
    if detail:
        form=session.get(ServiceFormVersion,item.form_version_id) if item.form_version_id else None
        data['form']=None if form is None else {'id':form.id,'title':form.title,'version':form.version,'schema':form.schema_json,'answers':item.form_answers}
        data['workflows']=[{'id':task.id,'agency_id':task.agency_id,'agency_name':name,'status':task.status,'version':task.version,'due_at':iso(task.due_at),'completed_at':iso(task.completed_at),'decision_note':task.decision_note,'overdue':bool(task.due_at and task.due_at<utcnow() and task.status in ('pending','processing'))} for task,name in session.execute(select(RequestWorkflow,Agency.name).join(Agency,Agency.id==RequestWorkflow.agency_id).where(RequestWorkflow.request_id==item.id).order_by(RequestWorkflow.agency_id))]
        classification=session.scalar(select(ClassificationResult).where(ClassificationResult.request_id==item.id)) if actor and actor.role=='admin' else None
        data['classification']=None if not classification else {'predicted_agency_code':classification.predicted_agency_code,'probabilities':classification.probabilities,'confidence':classification.confidence,'needs_review':classification.needs_review,'model_version':classification.model_version}
        events=session.scalars(select(RequestEvent).where(RequestEvent.request_id==item.id).order_by(RequestEvent.id)).all()
        data['events']=[{'id':e.id,'event_type':e.event_type,'from_status':e.from_status,'to_status':e.to_status,'note':e.note,'created_at':iso(e.created_at)} for e in events]
        from backend.app.models import RequestAttachment
        from backend.app.attachments.service import serialize_attachment
        att_rows=session.scalars(select(RequestAttachment).where(RequestAttachment.request_id==item.id).order_by(RequestAttachment.id.asc())).all()
        data['attachments']=[serialize_attachment(a,session.get(Agency,a.agency_id) if a.agency_id else None,session.get(User,a.uploaded_by)) for a in att_rows]
    return data
