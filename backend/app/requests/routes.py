from fastapi import APIRouter,Depends,Query,Request as HttpRequest
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User
from backend.app.auth.dependencies import get_current_user,require_role
from backend.app.requests.schemas import RequestCreate,StatusChange,Reroute
from backend.app.requests.service import scoped_query,get_request,submit_request,serialize
from backend.app.workflow.service import transition_request,reroute_request
from backend.app.workflow.schemas import TaskDecision,ReviewRoute
from backend.app.workflow.tasks import decide_task,review_route
from backend.app.ml.runtime import get_classifier

router=APIRouter(prefix='/requests',tags=['Permohonan'])


@router.post('',status_code=201)
def submit(payload: RequestCreate,request: HttpRequest,actor: User=Depends(require_role('citizen')),db: Session=Depends(get_session),classifier=Depends(get_classifier)):
    return serialize(db,submit_request(db,actor,payload,classifier),True,actor=actor)


@router.get('')
def listing(page: int=Query(1,ge=1),page_size: int=Query(20,ge=1,le=100),actor: User=Depends(get_current_user),db: Session=Depends(get_session)):
    query=scoped_query(actor)
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    items=db.scalars(query.order_by(query.column_descriptions[0]['entity'].id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {'items':[serialize(db,item) for item in items],'total':total,'page':page,'page_size':page_size}


@router.get('/{request_id}')
def detail(request_id: int,actor: User=Depends(get_current_user),db: Session=Depends(get_session)):
    return serialize(db,get_request(db,actor,request_id),True,actor=actor)


@router.patch('/{request_id}/status')
def change(request_id: int,payload: StatusChange,actor: User=Depends(require_role('staff','admin')),db: Session=Depends(get_session)):
    return serialize(db,transition_request(db,actor,request_id,payload.version,payload.status,payload.note),True,actor=actor)


@router.post('/{request_id}/reroute')
def reroute(request_id: int,payload: Reroute,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    return serialize(db,reroute_request(db,actor,request_id,payload.version,payload.agency_id,payload.note),True,actor=actor)


@router.patch('/{request_id}/tasks/{task_id}')
def decide(request_id:int,task_id:int,payload:TaskDecision,actor:User=Depends(require_role('staff')),db:Session=Depends(get_session)):
    return serialize(db,decide_task(db,actor,request_id,task_id,payload.request_version,payload.task_version,payload.status,payload.note),True,actor=actor)


@router.post('/{request_id}/review-route')
def review(request_id:int,payload:ReviewRoute,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return serialize(db,review_route(db,actor,request_id,payload.version,payload.agency_ids,payload.note),True,actor=actor)
