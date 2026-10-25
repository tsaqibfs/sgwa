import importlib.util
import pytest
from fastapi import HTTPException


@pytest.mark.parametrize('role,old,new,note,allowed',[
 ('staff','pending','processing','',True),
 ('staff','pending','approved','Selesai',False),
 ('staff','processing','approved','Dokumen lengkap',True),
 ('staff','processing','rejected','',False),
 ('staff','pending','escalated','Perlu koordinasi',True),
 ('admin','escalated','approved','Hasil review',True),
 ('admin','pending','approved','Override',False),
 ('citizen','pending','processing','',False),
 ('admin','approved','pending','Buka ulang',False),
 ('staff','processing','rejected','   ',False),
])
def test_allowed_transitions(role,old,new,note,allowed):
    assert importlib.util.find_spec('backend.app.workflow'), 'Workflow not implemented'
    from backend.app.workflow.service import validate_transition
    if allowed:
        validate_transition(role,old,new,note)
    else:
        with pytest.raises(HTTPException):
            validate_transition(role,old,new,note)


def test_submission_access_and_version_conflict(appdb):
    from backend.tests.conftest import register,login,seed_actor
    from sqlalchemy.orm import Session
    from backend.app.models import Agency
    client,engine,_=appdb
    with Session(engine) as db:
        agency=Agency(code='dukcapil',name='Dukcapil');db.add(agency);db.commit();agency_id=agency.id
    register(client);login(client)
    response=client.post('/api/v1/requests',json={'title':'Pengurusan KTP','description':'Saya ingin mengurus KTP dan kartu keluarga penduduk di Dukcapil.'})
    assert response.status_code==201,response.text
    request=response.json();assert request['status']=='pending'
    assert request['classification'] is None
    from sqlalchemy import select
    from backend.app.models import ClassificationResult
    with Session(engine) as db:
        assert db.scalar(select(ClassificationResult.confidence).where(ClassificationResult.request_id==request['id']))>=.60
    seed_actor(engine,'staff','staff@example.com',agency_id)
    login(client,'staff@example.com')
    url=f"/api/v1/requests/{request['id']}/status"
    assert client.patch(url,json={'version':1,'status':'processing','note':''}).status_code==200
    assert client.patch(url,json={'version':1,'status':'processing','note':''}).status_code==409
    assert client.patch(url,json={'version':2,'status':'approved','note':'Dokumen lengkap'}).status_code==200
    register(client,'other@example.com');login(client,'other@example.com')
    assert client.get(f"/api/v1/requests/{request['id']}").status_code==404


def test_rollback_and_inactive_routing(appdb):
    from backend.tests.conftest import register,login
    from sqlalchemy.orm import Session
    from sqlalchemy import select,func
    from backend.app.models import Agency,Request
    client,engine,app=appdb
    with Session(engine) as db:
        db.add(Agency(code='dukcapil',name='Dukcapil',active=False));db.commit()
    register(client);login(client)
    payload={'title':'Pengurusan KTP','description':'Saya ingin mengurus KTP dan kartu keluarga penduduk di Dukcapil.'}
    response=client.post('/api/v1/requests',json=payload)
    assert response.status_code==201
    assert response.json()['status']=='escalated'
    assert response.json()['assigned_agency_id'] is None
    app.state.classifier=None
    assert client.post('/api/v1/requests',json=payload).status_code==503
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Request))==1
