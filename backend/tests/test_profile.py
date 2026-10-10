import asyncio
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.tests.conftest import register, login
from backend.app.models import User, AuditLog
from backend.app.config import get_settings


def test_profile_update_rejects_privilege_fields(appdb):
    client, engine, _ = appdb
    register(client); login(client)
    response = client.patch('/api/v1/profile', json={'name': 'Nama Baru', 'phone': '081234', 'address': 'Jalan Kota'})
    assert response.status_code == 200
    assert response.json()['name'] == 'Nama Baru'
    for key in ('role', 'email', 'agency_id', 'id'):
        assert client.patch('/api/v1/profile', json={key: 'admin'}).status_code == 422
    for body in ({'name': ''}, {'name': None}, {'phone': 'x' * 31}, {'address': 'x' * 501}):
        assert client.patch('/api/v1/profile', json=body).status_code == 422
    assert client.patch('/api/v1/profile', json={'phone': None}).status_code == 200
    assert client.get('/api/v1/profile').json()['phone'] is None


def test_password_requires_current_and_different_value(appdb):
    client, engine, _ = appdb
    register(client); login(client)
    url = '/api/v1/profile/password'
    assert client.post(url, json={'current_password': 'WrongPassword123', 'new_password': 'NewPassword123!'}).status_code == 400
    assert client.post(url, json={'current_password': 'PasswordDemo123!', 'new_password': 'PasswordDemo123!'}).status_code == 422
    assert client.post(url, json={'current_password': 'PasswordDemo123!', 'new_password': 'short'}).status_code == 422
    assert client.get('/api/v1/auth/me').status_code == 200


def test_password_change_revokes_two_sessions_and_sse(appdb):
    client, engine, app = appdb
    register(client); login(client)
    old_token = client.cookies.get('sgwa_session')
    old_csrf = client.cookies.get('sgwa_csrf')
    with TestClient(app) as other:
        other.headers['Origin'] = 'http://testserver'
        other.headers['X-CSRF-Token'] = other.get('/api/v1/auth/csrf').json()['csrf_token']
        login(other)
        assert client.post('/api/v1/profile/password', json={'current_password': 'PasswordDemo123!', 'new_password': 'ChangedPassword123!'}).status_code == 200
        assert client.get('/api/v1/auth/me').status_code == 401
        assert other.get('/api/v1/auth/me').status_code == 401
        assert other.patch('/api/v1/profile', json={'name': 'Invalid session'}).status_code == 401
        other.get('/api/v1/auth/csrf')
        assert other.cookies.get('sgwa_session') is None
    from backend.app.live.service import iter_events
    async def check():
        stream = iter_events(engine, old_token, poll_seconds=0)
        assert 'session-invalid' in await anext(stream)
        await stream.aclose()
    asyncio.run(check())
    client.headers['X-CSRF-Token'] = client.get('/api/v1/auth/csrf').json()['csrf_token']
    assert login(client).status_code == 401
    assert login(client, password='ChangedPassword123!').status_code == 200
    with Session(engine) as db:
        assert db.scalar(select(User)).session_version == 2
        entries = db.scalars(select(AuditLog).where(AuditLog.action == 'profile.password_changed')).all()
        assert len(entries) == 1
        assert 'Password' not in str(entries[0].changes) and 'hash' not in str(entries[0].changes)


def test_old_jwt_without_version_rejected(appdb):
    client, _, _ = appdb
    register(client); user = login(client).json()['user']
    token = jwt.encode({'sub': str(user['id']), 'jti': 'old', 'kind': 'session', 'exp': datetime.now(timezone.utc) + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm='HS256')
    client.cookies.set('sgwa_session', token, domain='testserver.local', path='/')
    assert client.get('/api/v1/auth/me').status_code == 401


def test_concurrent_password_change_verifies_locked_hash(appdb):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from backend.app.profile.service import change_password
    from backend.app.profile.schemas import PasswordChange
    from fastapi import HTTPException
    client, engine, _ = appdb
    register(client); user_id = login(client).json()['user']['id']
    barrier = Barrier(2)
    def attempt(suffix):
        with Session(engine) as db:
            actor = db.get(User, user_id)
            barrier.wait(timeout=10)
            try:
                change_password(db, actor, PasswordChange(current_password='PasswordDemo123!', new_password=f'ChangedPassword{suffix}!'))
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(attempt, (1, 2))) == [200, 401]
