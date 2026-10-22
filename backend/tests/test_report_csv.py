import csv,io,importlib.util
from datetime import datetime
import pytest
from sqlalchemy import text,select,func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.tests.test_reports import report_case
from backend.tests.conftest import login
from backend.app.models import Request,RequestWorkflow,Agency,AuditLog,ClassificationResult

HEADERS=['nomor_permohonan','judul','status','dinas_utama','dinas_terlibat','diajukan_wib','diperbarui_wib','prediksi_dinas','confidence','versi_model']

def rows(response):
    assert response.status_code==200
    assert response.content.startswith(b'\xef\xbb\xbf')
    assert response.headers['content-type'].startswith('text/csv')
    assert response.headers['cache-control']=='no-store'
    assert response.headers['content-disposition'].startswith('attachment; filename="sgwa-laporan-')
    assert response.headers['x-report-generated-at'].endswith('Z')
    result=list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert result[0]==HEADERS
    return result[1:]

def test_csv_scope_companion_all_pages_and_empty(report_case):
    client,engine,_=report_case
    assert client.get('/api/v1/reports/requests.csv').status_code==401
    for uid,expected in [(1,{'REPORT-1','REPORT-2','REPORT-5'}),(2,{'REPORT-3','REPORT-4'}),(3,{'REPORT-1','REPORT-2'}),(4,{'REPORT-1','REPORT-3','REPORT-5'}),(5,set()),(6,{f'REPORT-{i}' for i in range(1,6)})]:
        login(client,f'report{uid}@test.id');assert {r[0] for r in rows(client.get('/api/v1/reports/requests.csv'))}==expected
    assert {r[0] for r in rows(client.get('/api/v1/reports/requests.csv?agency_id=2'))}=={'REPORT-1','REPORT-3','REPORT-5'}
    assert rows(client.get('/api/v1/reports/requests.csv?date_from=2026-11-01'))==[]
    for query in ['page=1','page_size=20','owner=1','status=wrong','agency_id=-1']:
        assert client.get('/api/v1/reports/requests.csv?'+query).status_code==422
    login(client,'report3@test.id');assert client.get('/api/v1/reports/requests.csv?agency_id=2').status_code==403
    login(client,'report7@test.id');assert client.get('/api/v1/reports/requests.csv').status_code==403
    with Session(engine) as db:
        db.add_all([Request(reference=f'PAGE-{i}',citizen_id=1,title='Judul page',description='Private text',created_at=datetime(2026,10,13),updated_at=datetime(2026,10,13)) for i in range(21)])
        db.commit()
    login(client,'report1@test.id');assert len(client.get('/api/v1/reports').json()['items'])==20
    assert len(rows(client.get('/api/v1/reports/requests.csv')))==24

def test_csv_exact_limit_and_overflow_no_truncation(report_case):
    client,engine,_=report_case;login(client,'report6@test.id')
    with Session(engine) as db:
        db.execute(Request.__table__.insert(),[{'reference':f'LIMIT-{i}','citizen_id':1,'title':'Permohonan batas','description':'Private','status':'pending','version':1,'created_at':datetime(2026,10,13),'updated_at':datetime(2026,10,13)} for i in range(4995)])
        db.add_all([Agency(id=i,code=f'extra{i}',name=f'Dinas {i}') for i in range(3,26)]);db.flush()
        db.add_all([RequestWorkflow(request_id=1,agency_id=i,status='pending') for i in range(3,26)])
        db.commit()
    assert len(rows(client.get('/api/v1/reports/requests.csv')))==5000
    with Session(engine) as db:
        db.add(Request(reference='LIMIT-OVER',citizen_id=1,title='Overflow',description='Private'));db.commit()
    response=client.get('/api/v1/reports/requests.csv')
    assert response.status_code==413 and response.headers['content-type'].startswith('application/json')
    assert 'content-disposition' not in response.headers
    with Session(engine) as db:assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action=='report.export_prepared'))==1

@pytest.mark.parametrize('value',['=1+1',' +cmd','\t=1','\rtext','\ntext','\ufeff \t@x','\x00 \ufeff-1','\u2003=SUM(1)'])
def test_csv_formula_prefixes(value):
    assert importlib.util.find_spec('backend.app.reports.csv_export'),'CSV exporter missing'
    from backend.app.reports.csv_export import safe_csv_cell
    assert safe_csv_cell(value)=="'"+value
    assert safe_csv_cell('Normal, "Indonesia"')=='Normal, "Indonesia"'

def test_csv_unicode_controls_bom_and_escaping(report_case):
    client,engine,_=report_case;login(client,'report6@test.id')
    title='Permohonan, "Jalan"\nDesa Indonesia — diperiksa'
    with engine.begin() as db:
        db.execute(text('UPDATE requests SET title=:title WHERE id=1'),{'title':title})
        db.execute(text("UPDATE agencies SET name='=SUM(1)' WHERE id=1"))
    result=next(r for r in rows(client.get('/api/v1/reports/requests.csv')) if r[0]=='REPORT-1')
    assert result[1]==title and result[3]=="'=SUM(1)" and result[4].startswith("'=SUM(1); Kesehatan")
    assert result[5]=='2026-10-13 01:00:00+07:00'
    assert result[7:]==['pajak','1.0','legacy-4']
    assert 'Private' not in str(result) and 'report1@test.id' not in str(result)

def test_export_audit_atomicity_and_history_unchanged(report_case,monkeypatch):
    client,engine,_=report_case;login(client,'report6@test.id')
    with engine.connect() as db:
        before={table:db.execute(text('SELECT * FROM '+table+' ORDER BY id')).all() for table in ['requests','classification_results','request_workflows','result_documents','ml_model_versions']}
    response=client.get('/api/v1/reports/requests.csv?status=pending');assert len(rows(response))==1
    with Session(engine) as db:
        log=db.scalar(select(AuditLog).where(AuditLog.action=='report.export_prepared'))
        assert log.entity_type=='report' and log.entity_id==0
        assert set(log.changes)=={'filters','count','generated_at'} and log.changes['count']==1
        assert log.changes['filters']['status']=='pending'
        assert 'Judul' not in str(log.changes)
    from backend.app.reports import csv_export
    def failure(*args,**kwargs):raise SQLAlchemyError('Test database unavailable')
    monkeypatch.setattr(csv_export,'record',failure)
    bad=client.get('/api/v1/reports/requests.csv')
    assert bad.status_code==503 and bad.headers['content-type'].startswith('application/json')
    assert 'content-disposition' not in bad.headers and 'Test database' not in bad.text
    with engine.connect() as db:
        for table,values in before.items():assert db.execute(text('SELECT * FROM '+table+' ORDER BY id')).all()==values
        assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action=='report.export_prepared'))==1
    monkeypatch.setattr(csv_export,'read_export_rows',failure)
    assert client.get('/api/v1/reports/requests.csv').status_code==503
