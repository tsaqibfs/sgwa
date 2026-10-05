from fastapi import APIRouter,Depends
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.models import User,Agency,Request
from backend.app.requests.service import scoped_query
from backend.app.db import get_session
from backend.app.auth.dependencies import get_current_user

router=APIRouter(prefix='/dashboard',tags=['Dashboard'])


@router.get('')
def dashboard(actor: User=Depends(get_current_user),db: Session=Depends(get_session)):
    scoped=scoped_query(actor).subquery()
    by_status=dict(db.execute(select(scoped.c.status,func.count()).group_by(scoped.c.status)).all())
    by_agency=[{'agency_id':agency_id,'name':name or 'Review admin','count':count} for agency_id,name,count in db.execute(select(scoped.c.assigned_agency_id,Agency.name,func.count()).outerjoin(Agency,Agency.id==scoped.c.assigned_agency_id).group_by(scoped.c.assigned_agency_id,Agency.name)).all()]
    return {'by_status':by_status,'by_agency':by_agency,'total':sum(by_status.values())}
