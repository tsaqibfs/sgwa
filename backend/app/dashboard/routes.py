from fastapi import APIRouter,Depends
from sqlalchemy import select,func,text
from sqlalchemy.orm import Session
from backend.app.models import User,Agency,Request,RequestWorkflow,utcnow
from backend.app.requests.service import scoped_query
from backend.app.db import get_session
from backend.app.auth.dependencies import get_current_user

router=APIRouter(prefix='/dashboard',tags=['Dashboard'])


@router.get('')
def dashboard(actor: User=Depends(get_current_user),db: Session=Depends(get_session)):
    scoped=scoped_query(actor).subquery()
    by_status=dict(db.execute(select(scoped.c.status,func.count()).group_by(scoped.c.status)).all())
    by_agency=[{'agency_id':agency_id,'name':name or 'Review admin','count':count} for agency_id,name,count in db.execute(select(RequestWorkflow.agency_id,Agency.name,func.count()).select_from(scoped).outerjoin(RequestWorkflow,RequestWorkflow.request_id==scoped.c.id).outerjoin(Agency,Agency.id==RequestWorkflow.agency_id).group_by(RequestWorkflow.agency_id,Agency.name)).all()]
    overdue=db.scalar(select(func.count(func.distinct(RequestWorkflow.request_id))).join(scoped,scoped.c.id==RequestWorkflow.request_id).where(RequestWorkflow.status.in_(['pending','processing']),RequestWorkflow.due_at<utcnow(),scoped.c.status.not_in(['approved','rejected'])))
    duration=db.scalar(select(func.avg(func.timestampdiff(text('SECOND'),scoped.c.created_at,scoped.c.updated_at)/3600)).where(scoped.c.status.in_(['approved','rejected'])))
    return {'by_status':by_status,'by_agency':by_agency,'total':sum(by_status.values()),'overdue_count':overdue,'average_completed_hours':float(duration) if duration is not None else None}
