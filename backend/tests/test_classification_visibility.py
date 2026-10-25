from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Agency,ClassificationResult
from backend.app.ml.schemas import Prediction
from backend.tests.conftest import register,login,seed_actor


def prepared(appdb):
    client,engine,app=appdb
    with Session(engine) as db:
        department=Agency(code='dukcapil',name='Dukcapil');db.add(department);db.commit();agency_id=department.id
    seed_actor(engine,'admin','admin@visibility.id')
    seed_actor(engine,'staff','staff@visibility.id',agency_id)
    class Fixed:
        def predict(self,text):return Prediction('dukcapil',{'dukcapil':.9},.9,True,'visibility-fixture',auto_routing_enabled=False)
    app.state.classifier=Fixed()
    register(client);login(client)
    response=client.post('/api/v1/requests',json={'title':'Permohonan KTP contoh','description':'Saya memerlukan penggantian KTP yang hilang dan informasi tindak lanjut.'})
    assert response.status_code==201,response.text
    return client,engine,response.json(),agency_id


def test_prediction_in_submission_and_detail_is_admin_only(appdb):
    c,engine,item,agency_id=prepared(appdb)
    assert item['classification'] is None
    assert c.get(f"/api/v1/requests/{item['id']}").json()['classification'] is None
    login(c,'admin@visibility.id')
    before=c.get(f"/api/v1/requests/{item['id']}").json()['classification']
    assert before['model_version']=='visibility-fixture' and before['confidence']==.9
    routed=c.post(f"/api/v1/requests/{item['id']}/review-route",json={'version':item['version'],'agency_ids':[agency_id],'note':'Teruskan ke Dukcapil setelah pemeriksaan.'})
    assert routed.status_code==200 and routed.json()['classification']==before
    login(c,'staff@visibility.id')
    detail=c.get(f"/api/v1/requests/{item['id']}")
    assert detail.status_code==200 and detail.json()['classification'] is None
    login(c)
    assert c.get(f"/api/v1/requests/{item['id']}").json()['classification'] is None
    with Session(engine) as db:
        prediction=db.scalar(select(ClassificationResult).where(ClassificationResult.request_id==item['id']))
        assert prediction.model_version=='visibility-fixture' and prediction.confidence==.9


def test_staff_mutations_hide_prediction_and_admin_mutations_preserve_it(appdb):
    c,engine,item,agency_id=prepared(appdb)
    login(c,'admin@visibility.id')
    item=c.post(f"/api/v1/requests/{item['id']}/reroute",json={'version':item['version'],'agency_id':agency_id,'note':'Penugasan admin.'}).json()
    prediction=item['classification'];assert prediction['model_version']=='visibility-fixture'
    login(c,'staff@visibility.id')
    response=c.patch(f"/api/v1/requests/{item['id']}/status",json={'version':item['version'],'status':'processing','note':''})
    assert response.status_code==200,response.text
    item=response.json();assert item['classification'] is None
    task=item['workflows'][0]
    response=c.patch(f"/api/v1/requests/{item['id']}/tasks/{task['id']}",json={'request_version':item['version'],'task_version':task['version'],'status':'escalated','note':'Perlu pemeriksaan lanjutan admin.'})
    assert response.status_code==200 and response.json()['classification'] is None
    item=response.json();login(c,'admin@visibility.id')
    response=c.patch(f"/api/v1/requests/{item['id']}/status",json={'version':item['version'],'status':'approved','note':'Diputuskan oleh admin.'})
    assert response.status_code==200 and response.json()['classification']==prediction
