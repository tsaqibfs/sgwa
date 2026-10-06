from sqlalchemy.orm import Session
from backend.app.models import Agency,AuditLog
from backend.tests.conftest import register,login,seed_actor
from backend.app.ml.schemas import Prediction


def prepared(appdb):
    client,engine,app=appdb
    with Session(engine) as db:
        a=Agency(code='perizinan',name='Perizinan');b=Agency(code='pajak',name='Pajak');db.add_all([a,b]);db.commit();ids=[a.id,b.id]
    seed_actor(engine,'admin','admin@test.id');login(client,'admin@test.id')
    client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':ids})
    class Fixed:
        def predict(self,text):return Prediction('perizinan',{'perizinan':.9,'pajak':.1},.9,True,'parallel-test')
    app.state.classifier=Fixed();register(client);login(client)
    item=client.post('/api/v1/requests',json={'title':'Permohonan usaha','description':'Saya mengurus perizinan usaha dan pajak atas usaha tersebut.'}).json()
    for i,email in zip(ids,['izin@test.id','pajak@test.id']):seed_actor(engine,'staff',email,i)
    return client,engine,item,ids


def decision(client,item,task,status,note='Hasil pemeriksaan dokumen'):
    return client.patch(f"/api/v1/requests/{item['id']}/tasks/{task['id']}",json={'request_version':item['version'],'task_version':task['version'],'status':status,'note':note})


def test_all_agencies_must_approve_and_access_is_scoped(appdb):
    c,engine,item,ids=prepared(appdb);login(c,'izin@test.id')
    task=item['workflows'][0]
    response=decision(c,item,task,'processing');assert response.status_code==200,response.text
    progressed=response.json()
    assert decision(c,item,task,'processing').status_code==409
    item=decision(c,progressed,progressed['workflows'][0],'approved').json()
    assert item['status']=='processing'
    login(c,'pajak@test.id')
    assert c.get(f"/api/v1/requests/{item['id']}").status_code==200
    assert c.get('/api/v1/requests').json()['total']==1
    assert decision(c,item,item['workflows'][0],'processing').status_code==404
    item=decision(c,item,item['workflows'][1],'processing').json()
    item=decision(c,item,item['workflows'][1],'approved').json()
    assert item['status']=='approved' and all(t['status']=='approved' for t in item['workflows'])


def test_rejection_freezes_tasks_and_review_preserves_old_outcomes(appdb):
    c,engine,item,ids=prepared(appdb);login(c,'izin@test.id')
    item=decision(c,item,item['workflows'][0],'processing').json()
    item=decision(c,item,item['workflows'][0],'rejected','Dokumen perlu diperbaiki').json()
    assert item['status']=='escalated'
    login(c,'pajak@test.id');assert decision(c,item,item['workflows'][1],'processing').status_code==409
    login(c,'admin@test.id')
    response=c.post(f"/api/v1/requests/{item['id']}/review-route",json={'version':item['version'],'agency_ids':ids,'note':'Mulai review ulang setelah perbaikan'})
    assert response.status_code==200,response.text
    fresh=response.json();assert fresh['status']=='pending' and all(t['status']=='pending' for t in fresh['workflows'])
    assert fresh['classification']==item['classification']
    assert any('Dokumen perlu diperbaiki' in e['note'] for e in fresh['events'])
    with Session(engine) as db:
        rows=db.query(AuditLog).filter_by(action='request.rerouted').all()
        assert rows[-1].changes['previous_workflows'][0]['status']=='rejected'
