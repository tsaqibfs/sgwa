import importlib.util
import os
import pytest


@pytest.fixture
def appdb():
    assert importlib.util.find_spec('backend.app.main'), 'API not implemented'
    from backend.app.config import get_settings
    from backend.app.db import get_engine
    from backend.app.models import Base
    from backend.app.main import create_app
    url=os.environ.get('TEST_DATABASE_URL','')
    if not url:
        pytest.skip('MySQL test connection not configured (TEST_DATABASE_URL)')
    assert url.rsplit('/',1)[-1].startswith('sgwa_test'), 'Use a dedicated sgwa_test database'
    os.environ['DATABASE_URL']=url
    os.environ['JWT_SECRET']='test-only-secret-of-at-least-32-characters-long'
    os.environ['TRUSTED_ORIGINS']='["http://testserver"]'
    get_settings.cache_clear();get_engine.cache_clear()
    engine=get_engine();Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    app=create_app()
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        client.headers['Origin']='http://testserver'
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        client.headers['X-CSRF-Token']=token
        yield client,engine,app
    Base.metadata.drop_all(engine);engine.dispose();get_engine.cache_clear();get_settings.cache_clear()


def register(client,email='warga@example.com',password='PasswordDemo123!'):
    return client.post('/api/v1/auth/register',json={'name':'Warga Demo','email':email,'password':password})


def login(client,email='warga@example.com',password='PasswordDemo123!'):
    response=client.post('/api/v1/auth/login',json={'email':email,'password':password})
    if response.status_code==200:
        client.headers['X-CSRF-Token']=response.json()['csrf_token']
    return response


def seed_actor(engine,role,email,agency_id=None):
    from sqlalchemy.orm import Session
    from backend.app.models import User
    from backend.app.auth.service import hash_password
    with Session(engine) as db:
        user=User(name=role,email=email,password_hash=hash_password('PasswordDemo123!'),role=role,agency_id=agency_id)
        db.add(user);db.commit();return user.id
