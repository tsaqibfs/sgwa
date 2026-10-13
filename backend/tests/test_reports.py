"""Real MySQL report behavior: scope, unique requests and snapshot semantics."""
import importlib.util
from contextlib import contextmanager
from datetime import date,datetime,timedelta
import pytest
from sqlalchemy import select,func,text,event
from sqlalchemy.orm import Session
from pydantic import ValidationError
from fastapi import HTTPException
from backend.app.models import User,Agency,Request,RequestWorkflow,ClassificationResult

NOW=datetime(2026,10,13,12)

def reports():
    assert importlib.util.find_spec('backend.app.reports'), 'Reports not implemented'
    from backend.app.reports import schemas,service
    return schemas,service

@pytest.fixture
def report_case(appdb):
    client,engine,app=appdb
    from backend.app.auth.service import hash_password
    password=hash_password('PasswordDemo123!')
    with Session(engine) as db:
        db.add_all([Agency(id=1,code='dukcapil',name='Dukcapil'),Agency(id=2,code='kesehatan',name='Kesehatan',active=False)])
        db.flush()
        for uid,role,agency in [(1,'citizen',None),(2,'citizen',None),(3,'staff',1),(4,'staff',2),(5,'staff',None),(6,'admin',None),(7,'unknown',None)]:
            db.add(User(id=uid,name='Pemohon '+str(uid),email=f'report{uid}@test.id',password_hash=password,role=role,agency_id=agency))
        db.flush()
        for rid,owner,status,agency,hours in [(1,1,'pending',1,0),(2,1,'approved',1,1),(3,2,'rejected',2,3),(4,2,'escalated',None,0),(5,1,'processing',2,0)]:
            created=datetime(2026,10,12,18)
            db.add(Request(id=rid,reference=f'REPORT-{rid}',citizen_id=owner,title='Judul '+str(rid),description='Private description',status=status,assigned_agency_id=agency,created_at=created,updated_at=created+timedelta(hours=hours)))
        db.flush()
        for rid,aid,status,due in [(1,1,'pending',-1),(1,2,'processing',1),(2,1,'approved',-1),(3,2,'pending',-1),(5,2,'processing',-1)]:
            db.add(RequestWorkflow(request_id=rid,agency_id=aid,status=status,due_at=NOW+timedelta(days=due)))
        db.add(ClassificationResult(request_id=1,predicted_agency_code='pajak',probabilities={'pajak':1},confidence=1,needs_review=False,model_version='legacy-4'))
        db.commit()
    return client,engine,app

def read(engine,uid,**values):
    schemas,service=reports()
    with Session(engine) as db:return service.read_report(db,db.get(User,uid),schemas.ReportQuery(**values),NOW)

def test_report_scope_filters_and_parallel_no_duplicates(report_case):
    _,engine,_=report_case
    for uid,expected in [(1,{1,2,5}),(2,{3,4}),(3,{1,2}),(4,{1,3,5}),(5,set()),(6,{1,2,3,4,5})]:
        result=read(engine,uid)
        assert {r.id for r in result.items}==expected and result.total==len(expected)
    result=read(engine,6,agency_id=2)
    assert {r.id for r in result.items}=={1,3,5} and result.total==3
    assert read(engine,3).filters.agency_id==1
    assert read(engine,1,agency_id=2).total==2
    assert read(engine,6,agency_id=999).total==0
    with pytest.raises(HTTPException) as exc:read(engine,3,agency_id=2)
    assert exc.value.status_code==403
    with pytest.raises(HTTPException) as exc:read(engine,7)
    assert exc.value.status_code==403

def test_wib_boundaries_and_strict_query_validation(report_case):
    schemas,service=reports();_,engine,_=report_case
    filters=schemas.ReportFilters(date_from=date(2026,10,13),date_to=date(2026,10,13))
    assert service.utc_bounds(filters)==(datetime(2026,10,12,17),datetime(2026,10,13,17))
    with engine.begin() as db:
        for rid,moment in [(1,datetime(2026,10,12,16,59,59)),(2,datetime(2026,10,12,17)),(3,datetime(2026,10,13,16,59,59)),(4,datetime(2026,10,13,17)),(5,datetime(2026,10,14))]:
            db.execute(text('UPDATE requests SET created_at=:moment WHERE id=:id'),{'id':rid,'moment':moment})
    assert {r.id for r in read(engine,6,**filters.model_dump()).items}=={2,3}
    for values in [{'date_from':'bad'},{'date_from':'2026-10-14','date_to':'2026-10-13'},{'status':'wrong'},{'page':0},{'page_size':101},{'agency_id':0},{'owner':1},{'date_from':'0001-01-01'}]:
        with pytest.raises(ValidationError):schemas.ReportQuery(**values)
    assert schemas.ReportQuery(date_to='9999-12-31').date_to==date(9999,12,31)

def test_summary_completion_duration_overdue_and_empty(report_case):
    _,engine,_=report_case
    result=read(engine,6);summary=result.summary
    assert summary.total==5 and summary.completed_count==2 and summary.completion_rate==0.4
    assert summary.by_status=={s:1 for s in ['pending','processing','escalated','approved','rejected']}
    assert summary.average_completed_hours==2 and summary.overdue_count==2
    assert read(engine,3).summary.overdue_count==1
    assert read(engine,4).summary.overdue_count==1
    assert read(engine,6,status='approved').summary.overdue_count==0
    assert read(engine,6,status='rejected').summary.completion_rate==1
    empty=read(engine,6,date_from=date(2026,11,1)).summary
    assert empty.total==0 and empty.completion_rate is None and empty.average_completed_hours is None
    with engine.begin() as db:db.execute(text('UPDATE requests SET updated_at=created_at-INTERVAL 1 HOUR WHERE id=2'))
    assert read(engine,6,status='approved').summary.average_completed_hours is None

def test_page_order_and_batch_projection(report_case):
    _,engine,_=report_case
    assert [r.id for r in read(engine,6,page_size=2).items]==[5,4]
    assert [r.id for r in read(engine,6,page=2,page_size=2).items]==[3,2]
    assert read(engine,6,page=100).items==[] and read(engine,6,page=100).total==5
    result=read(engine,6)
    first=next(r for r in result.items if r.id==1)
    assert first.primary_agency.id==1 and [a.id for a in first.agencies]==[1,2]
    assert first.classification.predicted_agency_code=='pajak' and first.classification.model_version=='legacy-4'
    assert next(r for r in result.items if r.id==4).primary_agency is None
    def queries(size):
        calls=[]
        def listen(*args):calls.append(args[2])
        event.listen(engine,'before_cursor_execute',listen)
        try:read(engine,6,page_size=size)
        finally:event.remove(engine,'before_cursor_execute',listen)
        return len([q for q in calls if q.lstrip().upper().startswith('SELECT')])
    assert queries(5)==queries(2)

def test_report_rr_snapshot_without_changing_auth_isolation(report_case):
    reports();_,engine,_=report_case
    from backend.app.reports.session import get_report_session
    with engine.connect() as connection:original=connection.get_isolation_level()
    with contextmanager(get_report_session)() as db:
        assert db.connection().get_isolation_level()=='REPEATABLE READ'
        assert db.scalar(select(func.count()).select_from(Request))==5
        with engine.begin() as writer:writer.execute(text("UPDATE requests SET title='Concurrent writer' WHERE id=1"))
        assert db.get(Request,1).title=='Judul 1'
        with engine.begin() as writer:
            writer.execute(text("INSERT INTO requests(id,reference,citizen_id,title,description,status,version,created_at,updated_at) VALUES(6,'REPORT-6',1,'Concurrent','Description','pending',1,'2026-10-13','2026-10-13')"))
        assert db.scalar(select(func.count()).select_from(Request))==5
    with engine.connect() as connection:assert connection.get_isolation_level()==original
    assert read(engine,6).total==6
