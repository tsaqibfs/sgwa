from fastapi import HTTPException
from sqlalchemy import update,select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from backend.app.models import Request,RequestEvent,User,Agency,utcnow
from backend.app.requests.service import get_request
from backend.app.audit.service import record


def validate_transition(role: str,old: str,new: str,note: str):
    if new in ('approved','rejected','escalated') and not note.strip():
        raise HTTPException(422,'Catatan keputusan wajib diisi.')
    allowed={'staff':{('pending','processing'),('processing','approved'),('processing','rejected'),('pending','escalated'),('processing','escalated')},'admin':{('escalated','approved'),('escalated','rejected')}}
    if (old,new) not in allowed.get(role,set()):
        raise HTTPException(409,'Perubahan status tidak diizinkan.')


def apply_change(session: Session,actor: User,item: Request,expected_version: int,new: str,note: str,agency_id: int|None,event_type: str):
    old=item.status
    old_agency=item.assigned_agency_id
    try:
        result=session.execute(update(Request).where(Request.id==item.id,Request.version==expected_version).values(status=new,assigned_agency_id=agency_id,version=Request.version+1,updated_at=utcnow()).execution_options(synchronize_session=False))
    except OperationalError as exc:
        if exc.orig.args[0] in (1020,1205,1213):
            session.rollback()
            raise HTTPException(409,'Perubahan bersamaan terdeteksi. Muat ulang permohonan.') from exc
        raise
    if result.rowcount!=1:
        session.rollback();raise HTTPException(409,'Permohonan sudah diperbarui. Muat ulang sebelum melanjutkan.')
    session.add(RequestEvent(request_id=item.id,actor_id=actor.id,event_type=event_type,from_status=old,to_status=new,note=note.strip()))
    record(session,actor.id,'request.'+event_type,'request',item.id,{'from_status':old,'to_status':new,'from_agency_id':old_agency,'to_agency_id':agency_id})
    session.commit();session.refresh(item)
    return item


def transition_request(session: Session,actor: User,request_id: int,expected_version: int,status: str,note: str) -> Request:
    item=get_request(session,actor,request_id)
    if item.version!=expected_version:
        raise HTTPException(409,'Permohonan sudah diperbarui. Muat ulang sebelum melanjutkan.')
    validate_transition(actor.role,item.status,status,note)
    return apply_change(session,actor,item,expected_version,status,note,item.assigned_agency_id,'status_changed')


def reroute_request(session: Session,actor: User,request_id: int,expected_version: int,agency_id: int,note: str) -> Request:
    if actor.role!='admin':
        raise HTTPException(403,'Hanya admin dapat mengalihkan permohonan.')
    item=get_request(session,actor,request_id)
    if item.version!=expected_version or item.status!='escalated':
        raise HTTPException(409,'Hanya kasus eskalasi terbaru dapat dialihkan.')
    agency=session.scalar(select(Agency).where(Agency.id==agency_id).with_for_update())
    if not agency or not agency.active or not note.strip():
        raise HTTPException(422,'Pilih dinas aktif dan isi alasan pengalihan.')
    return apply_change(session,actor,item,expected_version,'pending',note,agency_id,'rerouted')
