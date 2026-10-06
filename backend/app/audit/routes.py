from datetime import datetime,timezone
from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.models import AuditLog,User
from backend.app.db import get_session
from backend.app.auth.dependencies import require_role
from backend.app.requests.service import iso

router=APIRouter(prefix='/audit',tags=['Audit'])


@router.get('')
def audit(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),actor_id:int|None=Query(None,gt=0),action:str|None=Query(None,max_length=80),entity_type:str|None=Query(None,max_length=30),from_date:datetime|None=None,to_date:datetime|None=None,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    def utc(value):return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
    start=utc(from_date) if from_date else None;end=utc(to_date) if to_date else None
    if start and end and start>=end:raise HTTPException(422,'Batas akhir harus sesudah batas awal.')
    query=select(AuditLog,User.name).outerjoin(User,User.id==AuditLog.actor_id)
    for field,value in [(AuditLog.actor_id,actor_id),(AuditLog.action,action),(AuditLog.entity_type,entity_type)]:
        if value is not None:query=query.where(field==value)
    if start:query=query.where(AuditLog.created_at>=start)
    if end:query=query.where(AuditLog.created_at<end)
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    items=[{'id':r.id,'actor_id':r.actor_id,'actor_name':name,'action':r.action,'entity_type':r.entity_type,'entity_id':r.entity_id,'changes':r.changes,'created_at':iso(r.created_at)} for r,name in db.execute(query.order_by(AuditLog.id.desc()).offset((page-1)*page_size).limit(page_size))]
    return {'items':items,'total':total,'page':page,'page_size':page_size}
