from backend.tests.conftest import register,login,seed_actor


def test_new_agency_and_staff_management(appdb):
    client,engine,_=appdb
    register(client);login(client)
    assert client.post('/api/v1/agencies',json={'code':'pendidikan','name':'Dinas Pendidikan','description':'Sekolah'}).status_code==403
    seed_actor(engine,'admin','admin@example.com');login(client,'admin@example.com')
    response=client.post('/api/v1/agencies',json={'code':'pendidikan','name':'Dinas Pendidikan','description':'Sekolah'})
    assert response.status_code==201,response.text
    agency_id=response.json()['id']
    assert client.patch(f'/api/v1/agencies/{agency_id}',json={'code':'changed'}).status_code==422
    staff=client.post('/api/v1/staff',json={'name':'Petugas Sekolah','email':'sekolah@example.com','password':'PasswordDemo123!','agency_id':agency_id})
    assert staff.status_code==201
    metadata=client.get('/api/v1/ml/metadata').json()
    assert 'pendidikan' in metadata['unsupported_agencies']
    result=client.patch(f'/api/v1/agencies/{agency_id}',json={'active':False})
    assert result.status_code==200
    assert client.post('/api/v1/staff',json={'name':'Petugas Baru','email':'baru@example.com','password':'PasswordDemo123!','agency_id':agency_id}).status_code==422


def test_seed_is_idempotent_and_preserves_existing_password(appdb):
    from sqlalchemy import select,func
    from sqlalchemy.orm import Session
    from backend.app.models import User,Agency
    from backend.app.seed import seed
    client,engine,_=appdb
    with Session(engine) as db:
        seed(db,'PasswordDemo123!')
        initial=db.scalar(select(User.password_hash).where(User.email=='admin@demo.sgwa.id'))
        seed(db,'DifferentPassword123!')
        assert db.scalar(select(func.count()).select_from(User))==5
        assert db.scalar(select(func.count()).select_from(Agency))==25
        assert db.scalar(select(User.password_hash).where(User.email=='admin@demo.sgwa.id'))==initial
    assert login(client,'admin@demo.sgwa.id').status_code==200
