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


def transition_request(session: Session,actor: User,request_id: int,expected_version: int,status: str,note: str) -> Request:
    from backend.app.workflow.tasks import lock_request,decide_task,finish
    from backend.app.models import RequestWorkflow
    if actor.role=='staff':
        task=session.scalar(select(RequestWorkflow).where(RequestWorkflow.request_id==request_id,RequestWorkflow.agency_id==actor.agency_id))
        if not task:raise HTTPException(404,'Tugas dinas tidak ditemukan.')
        return decide_task(session,actor,request_id,task.id,expected_version,task.version,status,note)
    item=lock_request(session,actor,request_id,expected_version)
    validate_transition(actor.role,item.status,status,note)
    return finish(session,actor.id,item,status,note,'status_changed',{'human_review':True})


def reroute_request(session: Session,actor: User,request_id: int,expected_version: int,agency_id: int,note: str) -> Request:
    from backend.app.workflow.tasks import review_route
    return review_route(session,actor,request_id,expected_version,[agency_id],note)
