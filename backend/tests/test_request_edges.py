import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.tests.conftest import register,login,seed_actor
from backend.app.models import Agency,Request,AuditLog,User,ClassificationResult
from backend.app.ml.schemas import Prediction

PAYLOAD={'title':'Permohonan KTP','description':'Saya ingin mengurus KTP yang hilang beserta kartu keluarga.'}


@pytest.mark.parametrize('confidence,known,status',[(.60,True,'pending'),(.59,True,'escalated'),(.90,False,'escalated')])
def test_threshold_routes_or_escalates(appdb,confidence,known,status):
    client,engine,app=appdb
    with Session(engine) as db:
        db.add(Agency(code='dukcapil',name='Dukcapil'));db.commit()
    class FixedInference:
        def predict(self,text):
            return Prediction('dukcapil',{'dukcapil':confidence,'pajak':1-confidence},confidence,known,'threshold-fixture')
    app.state.classifier=FixedInference()
    register(client);login(client)
    response=client.post('/api/v1/requests',json=PAYLOAD)
    assert response.status_code==201,response.text
    assert response.json()['status']==status
    assert bool(response.json()['assigned_agency_id'])==(status=='pending')


def test_validation_and_staff_isolation(appdb):
    client,engine,_=appdb
    register(client);login(client)
    assert client.post('/api/v1/requests',json={**PAYLOAD,'title':'    '}).status_code==422
    assert client.post('/api/v1/requests',json={**PAYLOAD,'citizen_id':999}).status_code==422
    assert client.get('/api/v1/requests?page_size=101').status_code==422
    with Session(engine) as db:
        a=Agency(code='dukcapil',name='Dukcapil');b=Agency(code='pajak',name='Pajak');db.add_all([a,b]);db.commit();a_id,b_id=a.id,b.id
    item=client.post('/api/v1/requests',json=PAYLOAD).json()
    seed_actor(engine,'staff','otherstaff@example.com',b_id);login(client,'otherstaff@example.com')
    assert client.get(f"/api/v1/requests/{item['id']}").status_code==404
    assert client.get('/api/v1/requests').json()['total']==0
    assert client.get('/api/v1/dashboard').json()['total']==0


def test_audit_failure_rolls_back_submission(appdb,monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    import backend.app.requests.service as service
    client,engine,_=appdb
    register(client);login(client)
    def broken(*args,**kwargs):
        raise SQLAlchemyError('test fault')
    monkeypatch.setattr(service,'record',broken)
    response=client.post('/api/v1/requests',json=PAYLOAD)
    assert response.status_code==503
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Request))==0
        assert db.scalar(select(func.count()).select_from(AuditLog))==0


def test_new_agency_reroute_keeps_prediction_history(appdb):
    client,engine,_=appdb
    register(client);login(client)
    item=client.post('/api/v1/requests',json={'title':'Permintaan tidak dikenal','description':'zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq'}).json()
    assert item['status']=='escalated'
    seed_actor(engine,'admin','admin@example.com');login(client,'admin@example.com')
    agency=client.post('/api/v1/agencies',json={'code':'pendidikan','name':'Dinas Pendidikan'}).json()
    url=f"/api/v1/requests/{item['id']}/reroute"
    routed=client.post(url,json={'version':1,'agency_id':agency['id'],'note':'Berkaitan dengan sekolah'}).json()
    assert routed['status']=='pending'
    assert routed['classification']==item['classification']
    assert routed['events'][-1]['event_type']=='rerouted'
    client.patch(f"/api/v1/agencies/{agency['id']}",json={'active':False})
    assert client.get(f"/api/v1/requests/{item['id']}").json()['agency_name']=='Dinas Pendidikan'


def test_concurrent_decisions_have_one_winner(appdb):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from backend.app.workflow.service import transition_request
    client,engine,_=appdb
    with Session(engine) as db:
        agency=Agency(code='dukcapil',name='Dukcapil');db.add(agency);db.commit();agency_id=agency.id
    register(client);login(client)
    item=client.post('/api/v1/requests',json=PAYLOAD).json()
    staff_id=seed_actor(engine,'staff','staff@example.com',agency_id)
    barrier=Barrier(2)
    def change():
        with Session(engine) as db:
            actor=db.get(User,staff_id)
            db.get(Request,item['id'])
            barrier.wait(timeout=10)
            try:
                transition_request(db,actor,item['id'],1,'processing','')
                return 200
            except HTTPException as exc:
                db.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda _:change(),range(2)))
    assert sorted(outcomes)==[200,409]
