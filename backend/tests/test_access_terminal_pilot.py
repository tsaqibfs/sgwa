"""Uji 3 evidence: real endpoint handlers and isolated MySQL, synthetic fixtures.

Set SGWA_ACCESS_PILOT_OUTPUT to save the matrix and hashes. No live/demo DB is
used: appdb validates the sgwa_test* database before destructive fixture setup.
"""
import csv
import hashlib
import json
import os
from datetime import datetime,timezone
from pathlib import Path

import pytest
from sqlalchemy import select,text
from sqlalchemy.orm import Session

from backend.app.models import (Base,Agency,User,Request,RequestWorkflow,RequestEvent,
                               RequestAttachment,ResultDocument)
from backend.tests.conftest import login


@pytest.fixture
def test_classifier():
    class NoInference:
        def predict(self,*args):raise AssertionError('ML must not run during access/terminal evaluation')
    return NoInference()


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str,separators=(',',':')).encode()).hexdigest()


def test_access_and_terminal_matrix(appdb,tmp_path,monkeypatch):
    client,engine,_=appdb
    from backend.app.config import get_settings
    from backend.app.auth.service import hash_password
    from backend.app.results.service import ensure_result_document
    monkeypatch.setattr(get_settings(),'upload_dir',tmp_path)
    if os.environ.get('SGWA_ACCESS_PILOT_OUTPUT'):
        assert engine.url.database=='sgwa_test_service' and engine.url.port==3308
    password=hash_password('PasswordDemo123!')
    actors={'citizen_a':(1,'citizen',None),'citizen_b':(2,'citizen',None),
            'staff_a':(3,'staff',1),'staff_b':(4,'staff',2),'staff_unassigned':(5,'staff',None),'admin':(6,'admin',None)}
    with Session(engine) as db:
        db.add_all([Agency(id=1,code='dukcapil',name='Dinas A - Dukcapil'),Agency(id=2,code='kesehatan',name='Dinas B - Kesehatan')]);db.flush()
        db.add_all([User(id=uid,name=role,email=key+'@access.example.com',password_hash=password,role=role,agency_id=aid) for key,(uid,role,aid) in actors.items()]);db.flush()
        setup=[(1,1,1,'pending'),(2,2,2,'processing'),(3,1,1,'approved'),(4,1,1,'rejected'),(5,2,2,'approved'),(6,1,1,'pending'),(7,2,None,'escalated')]
        for rid,owner,aid,status in setup:
            db.add(Request(id=rid,reference=f'ACCESS-TEST-{rid}',citizen_id=owner,title=f'Fixture request {rid}',
                description='PRIVATE-B-SENTINEL' if rid in (2,5,7) else 'Synthetic fixture for authorization and terminal protection.',
                assigned_agency_id=aid,status=status,version=1))
        db.flush()
        tasks=[(1,1,1,'pending'),(2,2,2,'processing'),(3,3,1,'approved'),(4,4,1,'rejected'),(5,5,2,'approved'),(6,6,1,'pending'),(7,6,2,'pending')]
        db.add_all([RequestWorkflow(id=tid,request_id=rid,agency_id=aid,status=status,version=1,decision_note='Synthetic fixture decision') for tid,rid,aid,status in tasks])
        db.add_all([RequestEvent(request_id=rid,actor_id=6,event_type='fixture',from_status=None,to_status=status,note='Prepared test state; not a real service event') for rid,_,_,status in setup]);db.flush()
        for rid in (3,4,5):ensure_result_document(db,db.get(Request,rid))
        for aid,rid,owner,agency in [(1,1,1,1),(2,2,2,2)]:
            content=b'%PDF-1.4\nSynthetic access-test fixture only\n'
            (tmp_path/f'fixture_{aid}.pdf').write_bytes(content)
            db.add(RequestAttachment(id=aid,request_id=rid,agency_id=agency,uploaded_by=owner,filename=f'fixture_{aid}.pdf',stored_name=f'fixture_{aid}.pdf',content_type='application/pdf',size_bytes=len(content)))
        db.commit()

    # Snapshot every row/column in protected business tables, not only status.
    protected=('requests','request_workflows','request_events','classification_results',
               'result_documents','request_attachments','mock_checks','notifications','audit_logs')
    def snapshot():
        result={}
        with engine.connect() as conn:
            for name in protected:
                table=Base.metadata.tables[name]
                rows=[dict(row) for row in conn.execute(select(table).order_by(table.c.id)).mappings()]
                result[name]={'count':len(rows),'sha256':_digest(rows)}
        result['fixture_files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tmp_path.iterdir()) if p.is_file()}
        return result

    def case(key,actor,method,path,expected,group,payload=None,ids=None,files=False,change=False):
        return dict(case_id=key,actor=actor,method=method,path='/api/v1'+path,expected_status=expected,group=group,
                    payload=payload,expected_ids=ids,files=files,expect_change=change)
    status=lambda value,version=1:dict(version=version,status=value,note='Authorized synthetic test note')
    task=lambda value,version=1,task_version=1:dict(request_version=version,task_version=task_version,status=value,note='Authorized synthetic test note')
    routing=lambda agencies,version=1:dict(version=version,agency_ids=agencies,note='Synthetic route assignment')
    legacy=lambda agency,version=1:dict(version=version,agency_id=agency,note='Synthetic route assignment')
    cases=[
        case('D01','anonymous','GET','/requests/1',401,'authentication'),
        case('P01','staff_a','GET','/requests/1',200,'allowed_read'),
        case('P02','staff_b','GET','/requests/2',200,'allowed_read'),
        case('P03','admin','GET','/requests/2',200,'allowed_read'),
        case('P04','citizen_a','GET','/requests/1',200,'allowed_read'),
        case('P05','citizen_b','GET','/requests/2',200,'allowed_read'),
        case('P06','staff_a','GET','/requests/6',200,'shared_assignment_read'),
        case('P07','staff_b','GET','/requests/6',200,'shared_assignment_read'),
        case('P08','staff_a','GET','/requests/3/result',200,'allowed_result'),
        case('P09','citizen_a','GET','/requests/3/result',200,'allowed_result'),
        case('P10','admin','GET','/requests/5/result',200,'allowed_result'),
        case('P11','staff_a','GET','/requests/1/attachments',200,'allowed_attachment'),
        case('P12','staff_a','GET','/attachments/1/download',200,'allowed_attachment'),
        case('L01','staff_a','GET','/requests?page_size=100',200,'list_scope',ids=[1,3,4,6]),
        case('L02','staff_b','GET','/requests?page_size=100',200,'list_scope',ids=[2,5,6]),
        case('L03','staff_unassigned','GET','/requests?page_size=100',200,'list_scope',ids=[]),
        case('L04','citizen_a','GET','/requests?page_size=100',200,'list_scope',ids=[1,3,4,6]),
        case('L05','citizen_b','GET','/requests?page_size=100',200,'list_scope',ids=[2,5,7]),
        case('L06','admin','GET','/requests?page_size=100',200,'list_scope',ids=list(range(1,8))),
        case('L07','staff_a','GET','/requests?page_size=100&agency_id=2',200,'query_parameter_cannot_expand_scope',ids=[1,3,4,6]),
        case('D02','staff_a','GET','/requests/2',404,'cross_department_read'),
        case('D03','staff_a','GET','/requests/5',404,'cross_department_terminal_read'),
        case('D04','staff_b','GET','/requests/1',404,'cross_department_read'),
        case('D05','citizen_a','GET','/requests/2',404,'cross_citizen_read'),
        case('D06','staff_unassigned','GET','/requests/1',404,'unassigned_staff'),
        case('D07','staff_a','PATCH','/requests/2/status',404,'cross_department_mutation',status('approved')),
        case('D08','staff_b','PATCH','/requests/1/status',404,'cross_department_mutation',status('processing')),
        case('D09','staff_a','PATCH','/requests/2/tasks/2',404,'cross_department_task',task('approved')),
        case('D10','staff_b','PATCH','/requests/1/tasks/1',404,'cross_department_task',task('processing')),
        case('D11','staff_a','PATCH','/requests/6/tasks/7',404,'other_department_task_on_shared_request',task('processing')),
        case('D12','admin','PATCH','/requests/1/tasks/1',403,'role_restriction',task('processing')),
        case('D13','citizen_a','PATCH','/requests/1/status',403,'role_restriction',status('processing')),
        case('D14','staff_a','POST','/requests/2/reroute',403,'admin_only_reroute',legacy(1)),
        case('D15','staff_a','POST','/requests/2/review-route',403,'admin_only_reroute',routing([1])),
        case('D16','staff_a','GET','/requests/5/result',404,'cross_department_result'),
        case('D17','citizen_a','GET','/requests/5/result',404,'cross_citizen_result'),
        case('D18','staff_a','GET','/requests/2/attachments',403,'cross_department_attachment'),
        case('D19','staff_a','GET','/attachments/2/download',403,'cross_department_attachment'),
        case('D20','staff_a','DELETE','/attachments/2',403,'cross_department_attachment_delete'),
        case('D21','staff_a','POST','/requests/2/attachments',403,'cross_department_attachment_upload',files=True),
        case('D22','citizen_a','POST','/requests/2/attachments',403,'cross_citizen_attachment_upload',files=True),
        case('D23','staff_unassigned','PATCH','/requests/1/status',404,'unassigned_staff',status('processing')),
    ]
    for rid,label in [(3,'approved'),(4,'rejected')]:
        cases.extend([
            case(f'T{rid}1','staff_a','PATCH',f'/requests/{rid}/status',409,'terminal_'+label,status('processing')),
            case(f'T{rid}2','staff_a','PATCH',f'/requests/{rid}/tasks/{rid}',409,'terminal_'+label,task('processing')),
            case(f'T{rid}3','admin','PATCH',f'/requests/{rid}/status',409,'terminal_'+label,status('pending')),
            case(f'T{rid}4','admin','PATCH',f'/requests/{rid}/status',409,'terminal_'+label,status('processing')),
            case(f'T{rid}5','admin','POST',f'/requests/{rid}/reroute',409,'terminal_'+label,legacy(2)),
            case(f'T{rid}6','admin','POST',f'/requests/{rid}/review-route',409,'terminal_'+label,routing([2])),
        ])
    cases.extend([
        case('M01','staff_a','PATCH','/requests/1/tasks/1',200,'allowed_pending_to_processing',task('processing'),change=True),
        case('V01','staff_a','PATCH','/requests/1/tasks/1',409,'stale_version_replay',task('approved',1,1)),
        case('M02','staff_a','PATCH','/requests/1/tasks/1',200,'allowed_processing_to_approved',task('approved',2,2),change=True),
        case('T51','staff_a','PATCH','/requests/1/status',409,'terminal_created_through_api',status('processing',3)),
        case('M03','admin','POST','/requests/7/review-route',200,'allowed_admin_assignment',routing([1,2]),change=True),
        case('P13','staff_b','GET','/requests/7',200,'new_assignment_read'),
        case('M04','staff_a','PATCH','/requests/6/tasks/6',200,'allowed_own_task_on_shared_request',task('processing'),change=True),
    ])
    output=os.environ.get('SGWA_ACCESS_PILOT_OUTPUT')
    out=Path(output) if output else None
    if out:
        out.mkdir(parents=True,exist_ok=True)
        assert not (out/'cases.json').exists(),'Use a new run directory; preserve previous evidence'
        (out/'matrix_before_run.json').write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    now=datetime.now(timezone.utc).isoformat()
    with engine.connect() as connection:mysql_version=connection.scalar(text('SELECT VERSION()'))
    metadata=dict(started_at=now,fixture_provenance='synthetic test fixtures, not real resident data',
        database_name=engine.url.database,database_port=engine.url.port,mysql_version=mysql_version,
        transport='FastAPI TestClient / in-process HTTP over ASGI, real auth handlers and MySQL; not external network/browser',
        account_count=len(actors),agencies=['Dukcapil (A)','Kesehatan (B)'],prepared_request_count=7,
        schema='Current SQLAlchemy models via appdb fixture; not a migration or Docker image equivalence test',
        ml='Not exercised; inference guard fixture raises if called',protected_tables=list(protected),
        fixture_note='Terminal states seeded for negative cases; normal terminal creation also checked through actual API actions',
        source_sha256={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
            'backend/app/requests/routes.py','backend/app/requests/service.py','backend/app/workflow/tasks.py','backend/app/workflow/service.py',
            'backend/app/results/routes.py','backend/app/attachments/routes.py','backend/app/attachments/service.py',__file__)})
    results=[];last_actor=None
    for spec in cases:
        if spec['actor']=='anonymous':client.cookies.clear();last_actor=None
        elif last_actor!=spec['actor']:
            # Anonymous-control requests clear cookies; reacquire the legitimate
            # anonymous/session CSRF pair before attempting the next login.
            csrf=client.get('/api/v1/auth/csrf')
            assert csrf.status_code==200
            client.headers['X-CSRF-Token']=csrf.json()['csrf_token']
            auth=login(client,spec['actor']+'@access.example.com')
            assert auth.status_code==200,'Synthetic actor login failed'
            last_actor=spec['actor']
        before=snapshot()
        kwargs={'json':spec['payload']} if spec['payload'] is not None else {}
        if spec['files']:kwargs={'files':{'file':('denied_fixture.pdf',b'%PDF-1.4\nSynthetic denied upload\n','application/pdf')}}
        response=client.request(spec['method'],spec['path'],**kwargs)
        after=snapshot();changed=[name for name in before if before[name]!=after[name]]
        checks={'expected_http_status':response.status_code==spec['expected_status']}
        if spec['expect_change']:
            checks['request_and_history_changed']='requests' in changed and 'request_events' in changed
        else:checks['protected_database_and_files_unchanged']=not changed
        if spec['expected_ids'] is not None:
            body=response.json();checks['scoped_ids']=sorted(r['id'] for r in body['items'])==spec['expected_ids'];checks['scoped_total']=body['total']==len(spec['expected_ids'])
        if spec['expected_status']>=400:
            checks['no_private_fixture_leak']='PRIVATE-B-SENTINEL' not in response.text
            checks['not_csrf_rejection']='Validasi keamanan gagal' not in response.text
        if spec['case_id']=='M01':checks['correct_transition']=response.json().get('status')=='processing' and response.json().get('version')==2
        if spec['case_id']=='M02':
            checks['correct_terminal_transition']=response.json().get('status')=='approved' and response.json().get('version')==3
            with Session(engine) as db:checks['result_document_persisted']=db.scalar(select(ResultDocument.id).where(ResultDocument.request_id==1)) is not None
        if spec['case_id']=='M03':checks['assigned_both_agencies']=sorted(t['agency_id'] for t in response.json().get('workflows',[]))==[1,2] and response.json().get('status')=='pending'
        if spec['case_id']=='M04':
            with Session(engine) as db:
                own=db.get(RequestWorkflow,6);other=db.get(RequestWorkflow,7)
                checks['other_task_unchanged']=own.status=='processing' and own.version==2 and other.status=='pending' and other.version==1
        passed=all(checks.values())
        results.append(dict(**spec,actual_status=response.status_code,passed=passed,checks=checks,
            changed_tables=changed,before=before,after=after))
        if out:
            (out/'cases.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            metadata.update(completed_cases=len(results),passed_cases=sum(r['passed'] for r in results),failed_cases=sum(not r['passed'] for r in results))
            (out/'run_metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        assert passed,f"{spec['case_id']} actor={spec['actor']} {spec['method']} {spec['path']}: HTTP {response.status_code}, checks={checks}, changed={changed}"
    if out:
        flat=[dict(case_id=r['case_id'],group=r['group'],actor=r['actor'],method=r['method'],endpoint=r['path'],
            expected_http=r['expected_status'],actual_http=r['actual_status'],outcome='PASS' if r['passed'] else 'FAIL',
            expect_business_change=r['expect_change'],changed_tables=';'.join(r['changed_tables']),checks=json.dumps(r['checks'],sort_keys=True)) for r in results]
        with (out/'case_matrix.csv').open('w',encoding='utf-8-sig',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
        metadata['finished_at']=datetime.now(timezone.utc).isoformat();metadata['all_cases_passed']=all(r['passed'] for r in results)
        (out/'run_metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
