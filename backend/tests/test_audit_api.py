from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import AuditLog
from backend.tests.conftest import register,login,seed_actor


def test_audit_access_filters_and_auth_redaction(appdb):
    c,engine,_=appdb;register(c);login(c)
    assert c.get('/api/v1/audit').status_code==403
    assert login(c,password='IncorrectPassword').status_code==401
    c.post('/api/v1/auth/logout')
    c.headers['X-CSRF-Token']=c.get('/api/v1/auth/csrf').json()['csrf_token']
    seed_actor(engine,'admin','admin@test.id');admin=login(c,'admin@test.id').json()['user']['id']
    response=c.get('/api/v1/audit?page_size=1&action=auth.login');assert response.status_code==200,response.text
    data=response.json();assert data['total']>=2 and len(data['items'])==1
    assert c.get(f'/api/v1/audit?actor_id={admin}&action=auth.login').json()['total']==1
    assert c.get('/api/v1/audit?from_date=2030-01-01T00:00:00Z').json()['total']==0
    assert c.get('/api/v1/audit?page_size=101').status_code==422
    with Session(engine) as db:
        actions=db.scalars(select(AuditLog.action)).all()
        assert 'auth.login_failed' in actions and 'auth.logout' in actions
        for row in db.scalars(select(AuditLog)):
            assert not any(secret in str(row.changes) for secret in ['PasswordDemo','IncorrectPassword','warga@example.com','sgwa_session','csrf_token','password_hash'])
