from sqlalchemy.orm import Session
from backend.app.models import Agency
from backend.tests.conftest import register,login,seed_actor
from backend.app.ml.schemas import Prediction


def test_configured_parallel_route_and_invalid_rules(appdb):
    client,engine,app=appdb
    with Session(engine) as db:
        a=Agency(code='perizinan',name='Perizinan',sla_days=2);b=Agency(code='pajak',name='Pajak',sla_days=5)
        db.add_all([a,b]);db.commit();ids=[a.id,b.id]
    register(client);login(client)
    assert client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':ids}).status_code==403
    seed_actor(engine,'admin','admin@test.id');login(client,'admin@test.id')
    assert client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':[ids[1],ids[1]]}).status_code==422
    assert client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':[]}).status_code==422
    assert client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':[9999]}).status_code==422
    assert client.put('/api/v1/workflow/routes/perizinan',json={'agency_ids':[ids[1]]}).status_code==200
    class Fixed:
        def predict(self,text):return Prediction('perizinan',{'perizinan':.9,'pajak':.1},.9,True,'route-test')
    app.state.classifier=Fixed();login(client)
    payload={'title':'Pengajuan usaha','description':'Saya ingin mengurus perizinan usaha dan kewajiban pajak.'}
    item=client.post('/api/v1/requests',json=payload).json()
    assert len(item['workflows'])==2
    assert {t['agency_id'] for t in item['workflows']}==set(ids)
    assert item['classification'] is None
    login(client,'admin@test.id')
    assert client.get(f"/api/v1/requests/{item['id']}").json()['classification']['predicted_agency_code']=='perizinan'
    assert item['workflows'][0]['due_at']!=item['workflows'][1]['due_at']
    login(client,'admin@test.id');client.patch(f'/api/v1/agencies/{ids[1]}',json={'active':False});login(client)
    blocked=client.post('/api/v1/requests',json=payload).json()
    assert blocked['status']=='escalated' and blocked['workflows']==[]
