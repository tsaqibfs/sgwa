from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import User,Agency,WorkflowRoute
from backend.app.db import get_session
from backend.app.auth.dependencies import require_role
from backend.app.workflow.schemas import RouteUpdate
from backend.app.workflow.routing import set_route

router=APIRouter(prefix='/workflow',tags=['Workflow'])


@router.get('/routes')
def routes(actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return [{'source_code':a.code,'source_name':a.name,'active':a.active,'agency_ids':sorted(set(db.scalars(select(WorkflowRoute.agency_id).where(WorkflowRoute.source_code==a.code)))|{a.id})} for a in db.scalars(select(Agency).order_by(Agency.name))]


@router.put('/routes/{code}')
def update_route(code:str,payload:RouteUpdate,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return {'source_code':code,'agency_ids':[a.id for a in set_route(db,actor,code,payload.agency_ids)]}
