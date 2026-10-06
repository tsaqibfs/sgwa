from fastapi import HTTPException
from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from backend.app.models import Agency,WorkflowRoute,User
from backend.app.audit.service import record


def locked_agencies(db:Session)->dict[int,Agency]:
    # A single consistent order protects routing against edits/deactivation.
    return {a.id:a for a in db.scalars(select(Agency).order_by(Agency.id).with_for_update().execution_options(populate_existing=True))}


def resolve_route(db:Session,code:str)->list[Agency]:
    agencies=locked_agencies(db)
    primary=next((a for a in agencies.values() if a.code==code),None)
    if not primary or not primary.active:return []
    ids=set(db.scalars(select(WorkflowRoute.agency_id).where(WorkflowRoute.source_code==code).with_for_update()))|{primary.id}
    if any(i not in agencies or not agencies[i].active for i in ids):return []
    return [primary]+[agencies[i] for i in sorted(ids-{primary.id})]


def set_route(db:Session,actor:User,code:str,agency_ids:list[int])->list[Agency]:
    if actor.role!='admin':raise HTTPException(403,'Hanya admin dapat mengatur rute.')
    agencies=locked_agencies(db);primary=next((a for a in agencies.values() if a.code==code),None)
    if not primary or not primary.active or not agency_ids or len(agency_ids)!=len(set(agency_ids)):
        raise HTTPException(422,'Pilih kode sumber aktif dan dinas tujuan yang unik.')
    ids=set(agency_ids)|{primary.id}
    if len(ids)>20 or any(i not in agencies or not agencies[i].active for i in ids):raise HTTPException(422,'Pilih maksimal 20 dinas aktif.')
    db.execute(delete(WorkflowRoute).where(WorkflowRoute.source_code==code))
    db.add_all([WorkflowRoute(source_code=code,agency_id=i) for i in sorted(ids)])
    record(db,actor.id,'workflow.route_updated','agency',primary.id,{'source_code':code,'agency_ids':sorted(ids)})
    db.commit()
    return [primary]+[agencies[i] for i in sorted(ids-{primary.id})]
