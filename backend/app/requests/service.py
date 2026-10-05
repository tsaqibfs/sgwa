import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Request,Agency,ClassificationResult,RequestEvent,User
from backend.app.audit.service import record
from backend.app.ml.classifier import Classifier,ModelUnavailable
from backend.app.requests.schemas import RequestCreate


def scoped_query(actor: User):
    query=select(Request)
    if actor.role=='citizen':
        return query.where(Request.citizen_id==actor.id)
    if actor.role=='staff':
        return query.where(Request.assigned_agency_id==actor.agency_id) if actor.agency_id else query.where(False)
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
    agency=session.scalar(select(Agency).where(Agency.code==prediction.agency_code,Agency.active.is_(True)))
    review=prediction.confidence<.60 or not prediction.known_features or agency is None
    item=Request(reference='SGWA-'+uuid.uuid4().hex[:16].upper(),citizen_id=actor.id,title=payload.title,description=payload.description,assigned_agency_id=None if review else agency.id,status='escalated' if review else 'pending')
    session.add(item);session.flush()
    session.add(ClassificationResult(request_id=item.id,predicted_agency_code=prediction.agency_code,probabilities=prediction.probabilities,confidence=prediction.confidence,needs_review=review,model_version=prediction.model_version))
    session.add(RequestEvent(request_id=item.id,actor_id=actor.id,event_type='submitted',from_status=None,to_status=item.status,note='Perlu pemeriksaan manual.' if review else 'Diteruskan berdasarkan klasifikasi ML.'))
    record(session,actor.id,'request.submitted','request',item.id,{'status':item.status,'assigned_agency_id':item.assigned_agency_id})
    session.commit()
    return item


def iso(value):
    return value.isoformat()+'Z' if value else None


def serialize(session: Session,item: Request,detail=False):
    agency=session.get(Agency,item.assigned_agency_id) if item.assigned_agency_id else None
    data={'id':item.id,'reference':item.reference,'citizen_id':item.citizen_id,'title':item.title,'description':item.description,'assigned_agency_id':item.assigned_agency_id,'agency_name':agency.name if agency else None,'status':item.status,'version':item.version,'created_at':iso(item.created_at),'updated_at':iso(item.updated_at)}
    if detail:
        classification=session.scalar(select(ClassificationResult).where(ClassificationResult.request_id==item.id))
        data['classification']=None if not classification else {'predicted_agency_code':classification.predicted_agency_code,'probabilities':classification.probabilities,'confidence':classification.confidence,'needs_review':classification.needs_review,'model_version':classification.model_version}
        events=session.scalars(select(RequestEvent).where(RequestEvent.request_id==item.id).order_by(RequestEvent.id)).all()
        data['events']=[{'id':e.id,'event_type':e.event_type,'from_status':e.from_status,'to_status':e.to_status,'note':e.note,'created_at':iso(e.created_at)} for e in events]
    return data
