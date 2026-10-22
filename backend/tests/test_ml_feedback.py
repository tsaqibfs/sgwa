import copy
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.models import Agency, Request, ClassificationResult, ResultDocument, AuditLog
from backend.tests.conftest import seed_actor, login

PAYLOAD={'expected_revision':0,'training_text':'Mohon bantuan beasiswa untuk siswa sekolah.','corrected_code':'pendidikan',
         'provenance':'synthetic_demo','reason':'Permohonan tentang sekolah, bukan KTP.','idempotency_key':'feedback-case-1'}


@pytest.fixture
def feedback_case(appdb):
    client,engine,app=appdb
    admin_id=seed_actor(engine,'admin','ml-admin@test.id')
    citizen=seed_actor(engine,'citizen','ml-citizen@test.id')
    seed_actor(engine,'staff','ml-staff@test.id')
    with Session(engine) as db:
        db.add_all([Agency(code='dukcapil',name='Dukcapil'),Agency(code='pendidikan',name='Pendidikan')]);db.flush()
        item=Request(reference='FEEDBACK-TEST',citizen_id=citizen,title='Beasiswa siswa',description='Saya ingin bantuan beasiswa sekolah.',status='approved')
        db.add(item);db.flush();request_id=item.id
        db.add(ClassificationResult(request_id=item.id,predicted_agency_code='dukcapil',probabilities={'dukcapil':.9,'pendidikan':.1},confidence=.9,needs_review=False,model_version='legacy-version'))
        db.add(ResultDocument(request_id=item.id,number='SGWA-DEMO-FEEDBACK',snapshot={'status':'approved','immutable':True}))
        db.commit()
    login(client,'ml-admin@test.id')
    return client,engine,request_id,admin_id


def test_admin_feedback_snapshot_verification_revision_and_history(feedback_case):
    client,engine,request_id,actor=feedback_case
    before=client.get(f'/api/v1/requests/{request_id}').json()
    url=f'/api/v1/ml/requests/{request_id}/feedback'
    response=client.post(url,json=PAYLOAD)
    assert response.status_code==201,response.text
    row=response.json()
    assert row['status']=='pending' and row['revision']==1 and row['created_by']==actor
    assert row['original_text']=='Beasiswa siswa Saya ingin bantuan beasiswa sekolah.'
    assert row['original_prediction']['model_version']=='legacy-version'
    assert client.post(url,json=PAYLOAD).json()['id']==row['id']
    assert client.post(url,json={**PAYLOAD,'reason':'Different payload'}).status_code==409
    review=client.post(f"/api/v1/ml/feedback/{row['id']}/review",json={'expected_revision':1,'decision':'verified','note':'Kelas sekolah sudah diperiksa.'})
    assert review.status_code==200 and review.json()['status']=='verified'
    revision=client.post(url,json={**PAYLOAD,'expected_revision':1,'idempotency_key':'feedback-case-2','training_text':'Saya membutuhkan bantuan biaya pendidikan sekolah.'})
    assert revision.status_code==201 and revision.json()['revision']==2
    history=client.get(f"/api/v1/ml/feedback/{row['id']}").json()
    assert history['status']=='superseded' and history['reviewed_by']==actor
    assert client.post(f"/api/v1/ml/feedback/{row['id']}/review",json={'expected_revision':1,'decision':'rejected','note':'Sudah ada revisi.'}).status_code==409
    assert client.post(url,json={**PAYLOAD,'idempotency_key':'feedback-case-3'}).status_code==409
    assert client.get(f'/api/v1/requests/{request_id}').json()==before
    with Session(engine) as db:
        assert db.scalar(select(ResultDocument.snapshot).where(ResultDocument.request_id==request_id))=={'status':'approved','immutable':True}
        assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action.like('ml.feedback%')))>=3


def test_feedback_authorization_csrf_and_payload_validation(feedback_case):
    client,_,request_id,_=feedback_case
    url=f'/api/v1/ml/requests/{request_id}/feedback'
    for patch in ({'provenance':None},{'training_text':' '*15},{'reason':'   '},{'corrected_code':'pajak'},{'created_by':1},{'family_key':'../../outside'}):
        assert client.post(url,json={**PAYLOAD,**patch}).status_code==422
    assert client.get('/api/v1/ml/feedback?page_size=101').status_code==422
    token=client.headers.pop('X-CSRF-Token')
    assert client.post(url,json=PAYLOAD).status_code==403
    client.headers['X-CSRF-Token']=token
    for email in ('ml-citizen@test.id','ml-staff@test.id'):
        login(client,email)
        assert client.post(url,json=PAYLOAD).status_code==403
        assert client.get('/api/v1/ml/feedback').status_code==403


def test_feedback_audit_failure_rolls_back(feedback_case,monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import backend.app.ml.feedback as service
    from backend.app.models import MLFeedback
    client,engine,request_id,_=feedback_case
    def broken(*args,**kwargs):raise SQLAlchemyError('feedback audit fault')
    monkeypatch.setattr(service,'record',broken)
    response=client.post(f'/api/v1/ml/requests/{request_id}/feedback',json=PAYLOAD)
    assert response.status_code==503
    with Session(engine) as db:assert db.scalar(select(func.count()).select_from(MLFeedback))==0


def test_concurrent_feedback_expected_revision_has_one_winner(feedback_case):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi import HTTPException
    from backend.app.ml.feedback import create_feedback
    from backend.app.ml.schemas import FeedbackCreate
    from backend.app.models import User,MLFeedback
    _,engine,request_id,actor_id=feedback_case
    def write(key):
        with Session(engine) as db:
            try:
                row=create_feedback(db,db.get(User,actor_id),request_id,FeedbackCreate(**{**PAYLOAD,'idempotency_key':key}))
                return row.revision
            except HTTPException as e:
                db.rollback();return e.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:answers=list(pool.map(write,['parallel-a','parallel-b']))
    assert sorted(answers)==[1,409]
    with Session(engine) as db:assert db.scalar(select(func.count()).select_from(MLFeedback))==1
