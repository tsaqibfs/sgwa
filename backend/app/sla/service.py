from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import RequestWorkflow,Request
from backend.app.workflow.tasks import finish


def escalate_overdue(db:Session,now:datetime,limit:int=100)->int:
    ids=db.scalars(select(RequestWorkflow.request_id).join(Request,Request.id==RequestWorkflow.request_id).where(RequestWorkflow.status.in_(['pending','processing']),RequestWorkflow.due_at<now,Request.status.in_(['pending','processing'])).distinct().order_by(RequestWorkflow.request_id).limit(limit)).all()
    count=0
    for request_id in ids:
        item=db.scalar(select(Request).where(Request.id==request_id).with_for_update().execution_options(populate_existing=True))
        if not item or item.status not in ('pending','processing'):
            db.rollback();continue
        overdue=db.scalars(select(RequestWorkflow).where(RequestWorkflow.request_id==request_id,RequestWorkflow.status.in_(['pending','processing']),RequestWorkflow.due_at<now).order_by(RequestWorkflow.id).with_for_update().execution_options(populate_existing=True)).all()
        if not overdue:
            db.rollback();continue
        finish(db,None,item,'escalated','SLA terlewati pada dinas: '+', '.join(str(t.agency_id) for t in overdue)+'. Menunggu pemeriksaan admin.','sla_escalated',{'overdue_agencies':[t.agency_id for t in overdue],'deadlines':[t.due_at.isoformat()+'Z' for t in overdue]})
        count+=1
    return count
