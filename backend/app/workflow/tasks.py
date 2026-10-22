from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select,update,delete
from sqlalchemy.orm import Session
from backend.app.models import Request,RequestWorkflow,RequestEvent,User,utcnow
from backend.app.requests.service import scoped_query
from backend.app.workflow.routing import locked_agencies
from backend.app.audit.service import record


def lock_request(db:Session,actor:User,request_id:int,version:int)->Request:
    item=db.scalar(scoped_query(actor).where(Request.id==request_id).with_for_update().execution_options(populate_existing=True))
    if not item:raise HTTPException(404,'Permohonan tidak ditemukan.')
    if item.version!=version:raise HTTPException(409,'Permohonan sudah diperbarui. Muat ulang sebelum melanjutkan.')
    return item


def finish(db:Session,actor_id:int|None,item:Request,status:str,note:str,event_type:str,changes:dict|None=None)->Request:
    old=item.status
    result=db.execute(update(Request).where(Request.id==item.id,Request.version==item.version).values(status=status,version=Request.version+1,updated_at=utcnow()).execution_options(synchronize_session=False))
    if result.rowcount!=1:raise HTTPException(409,'Perubahan bersamaan terdeteksi. Muat ulang permohonan.')
    db.add(RequestEvent(request_id=item.id,actor_id=actor_id,event_type=event_type,from_status=old,to_status=status,note=note.strip()))
    record(db,actor_id,'request.'+event_type,'request',item.id,{'from_status':old,'to_status':status,**(changes or {})})
    db.flush();db.refresh(item)
    from backend.app.notifications.service import notify_request_event
    agencies=list(db.scalars(select(RequestWorkflow.agency_id).where(RequestWorkflow.request_id==item.id)))
    notify_request_event(db,item,f'request:{item.id}:{item.version}:{event_type}',event_type,agencies)
    from backend.app.results.service import ensure_result_document
    ensure_result_document(db,item)
    db.commit();db.refresh(item)
    return item


def decide_task(db:Session,actor:User,request_id:int,task_id:int,request_version:int,task_version:int,status:str,note:str)->Request:
    if actor.role!='staff':raise HTTPException(403,'Keputusan dinas hanya dilakukan staf dinas terkait.')
    item=lock_request(db,actor,request_id,request_version)
    tasks=db.scalars(select(RequestWorkflow).where(RequestWorkflow.request_id==item.id).order_by(RequestWorkflow.id).with_for_update().execution_options(populate_existing=True)).all()
    task=next((t for t in tasks if t.id==task_id and t.agency_id==actor.agency_id),None)
    if not task:raise HTTPException(404,'Tugas dinas tidak ditemukan.')
    if item.status in ('escalated','approved','rejected') or task.version!=task_version:
        raise HTTPException(409,'Tugas tidak dapat diubah. Muat ulang kondisi terbaru.')
    if status in ('approved','rejected','escalated') and not note.strip():raise HTTPException(422,'Catatan keputusan wajib diisi.')
    allowed={('pending','processing'),('processing','approved'),('processing','rejected'),('pending','escalated'),('processing','escalated')}
    if (task.status,status) not in allowed:raise HTTPException(409,'Perubahan status tidak diizinkan.')
    previous=task.status
    task.version+=1;task.updated_at=utcnow();task.decision_note=note.strip()
    if status!='escalated':task.status=status
    if status in ('approved','rejected'):task.completed_at=utcnow()
    statuses=[t.status for t in tasks]
    aggregate='escalated' if status=='escalated' or 'rejected' in statuses else 'approved' if all(s=='approved' for s in statuses) else 'pending' if all(s=='pending' for s in statuses) else 'processing'
    return finish(db,actor.id,item,aggregate,f'Dinas #{task.agency_id}: {status}. {note}','task_updated',{'task_id':task.id,'agency_id':task.agency_id,'task_from_status':previous,'task_to_status':status})


def review_route(db:Session,actor:User,request_id:int,version:int,agency_ids:list[int],note:str)->Request:
    if actor.role!='admin':raise HTTPException(403,'Hanya admin dapat mengalihkan permohonan.')
    item=lock_request(db,actor,request_id,version)
    if item.status!='escalated':raise HTTPException(409,'Hanya kasus eskalasi terbaru dapat dialihkan.')
    if not note.strip() or not agency_ids or len(agency_ids)!=len(set(agency_ids)) or len(agency_ids)>20:raise HTTPException(422,'Pilih dinas unik dan isi alasan pengalihan.')
    agencies=locked_agencies(db)
    if any(i not in agencies or not agencies[i].active for i in agency_ids):raise HTTPException(422,'Pilih dinas aktif.')
    previous=[{'agency_id':t.agency_id,'status':t.status,'note':t.decision_note,'completed_at':t.completed_at.isoformat()+'Z' if t.completed_at else None} for t in db.scalars(select(RequestWorkflow).where(RequestWorkflow.request_id==item.id).order_by(RequestWorkflow.agency_id).with_for_update())]
    db.execute(delete(RequestWorkflow).where(RequestWorkflow.request_id==item.id))
    now=utcnow()
    db.add_all([RequestWorkflow(request_id=item.id,agency_id=i,due_at=now+timedelta(days=agencies[i].sla_days)) for i in sorted(agency_ids)])
    item.assigned_agency_id=agency_ids[0]
    archive='; '.join(f"Dinas #{t['agency_id']}: {t['status']} — {t['note']}" for t in previous)
    return finish(db,actor.id,item,'pending',note+(' | Putaran sebelumnya: '+archive if archive else ''),'rerouted',{'previous_workflows':previous,'to_agency_ids':agency_ids})
