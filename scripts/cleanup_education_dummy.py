"""Remove only the Education fixture created by the browser demo test."""
import re
from sqlalchemy import select,delete,or_,text
from sqlalchemy.orm import Session
from backend.app.db import get_engine
from backend.app.models import Agency,User,Request,RequestWorkflow,WorkflowRoute,RequestEvent,ClassificationResult
from backend.app.audit.service import record

def cleanup(db):
    agencies=[a for a in db.scalars(select(Agency).with_for_update()) if re.fullmatch(r'pendidikan_\d+',a.code) and a.name.startswith('Dinas Pendidikan Demo ')]
    ids=[a.id for a in agencies]
    if not ids:return {'agencies':0,'requests':0}
    if db.scalar(select(User.id).where(User.agency_id.in_(ids)).limit(1)):
        raise RuntimeError('Dummy memiliki akun staf; tidak dihapus otomatis.')
    task_requests=select(RequestWorkflow.request_id).where(RequestWorkflow.agency_id.in_(ids))
    items=db.scalars(select(Request).where(or_(Request.assigned_agency_id.in_(ids),Request.id.in_(task_requests))).with_for_update()).all()
    for item in items:
        owner=db.get(User,item.citizen_id)
        if item.title!='zzzzz qqqqq xxxxx' or item.description!='zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq' or owner.email!='warga@demo.sgwa.id':
            raise RuntimeError('Ada pengajuan di luar fixture yang dikenal; transaksi dibatalkan.')
    request_ids=[r.id for r in items]
    if request_ids:
        for model in [RequestWorkflow,RequestEvent,ClassificationResult]:
            db.execute(delete(model).where(model.request_id.in_(request_ids)))
        db.execute(delete(Request).where(Request.id.in_(request_ids)))
    db.execute(delete(WorkflowRoute).where(or_(WorkflowRoute.agency_id.in_(ids),WorkflowRoute.source_code.in_([a.code for a in agencies]))))
    db.execute(delete(Agency).where(Agency.id.in_(ids)))
    counts={'agencies':len(ids),'requests':len(request_ids)}
    record(db,None,'demo.education_cleaned','agency',0,{'agency_ids':ids,'request_ids':request_ids,**counts})
    return counts

if __name__=='__main__':
    with Session(get_engine()) as db:
        print('Database:',db.execute(text('SELECT VERSION(), @@version_comment')).one())
        counts=cleanup(db);db.commit();print('Dummy dihapus:',counts)
