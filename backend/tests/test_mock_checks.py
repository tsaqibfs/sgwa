from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.tests.test_parallel_decisions import prepared
from backend.tests.conftest import login
from backend.app.models import User, Request


def test_mock_types_scenarios_scope_and_idempotency(appdb, monkeypatch):
    import httpx
    def forbidden(*args, **kwargs): raise AssertionError('External network forbidden')
    monkeypatch.setattr(httpx, 'get', forbidden); monkeypatch.setattr(httpx, 'post', forbidden)
    c, engine, item, ids = prepared(appdb)
    url = f"/api/v1/requests/{item['id']}/mock-checks"
    assert c.get(url).status_code == 403
    assert c.post(url, json={'check_type': 'identity', 'scenario': 'success', 'idempotency_key': 'citizen-key'}).status_code == 403
    login(c, 'izin@test.id')
    for kind in ['identity', 'permit_completeness', 'general_service']:
        for scenario in ['success', 'mismatch', 'unavailable']:
            payload = {'check_type': kind, 'scenario': scenario, 'idempotency_key': kind+'-'+scenario}
            response = c.post(url, json=payload)
            assert response.status_code == 200, response.text
            check = response.json()
            assert check['outcome'] == scenario and check['payload']['simulation'] is True
            assert c.post(url, json=payload).json()['id'] == check['id']
            assert c.post(url, json={**payload, 'scenario': 'mismatch' if scenario == 'success' else 'success'}).status_code == 409
    assert len(c.get(url).json()) == 9
    assert c.get(f"/api/v1/requests/{item['id']}").json()['version'] == 1
    assert c.post(url, json={'check_type': 'unknown', 'scenario': 'success', 'idempotency_key': 'unknown'}).status_code == 422
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == 'izin@test.id')); user.agency_id = None; db.commit()
    assert c.get(url).status_code == 404


def test_mock_key_cannot_move_between_requests_and_concurrent_retry(appdb):
    c, engine, item, ids = prepared(appdb)
    second = c.post('/api/v1/requests', json={'title': 'Izin lainnya', 'description': 'Saya mengurus perizinan usaha dan pajak atas usaha tersebut.'}).json()
    login(c, 'izin@test.id')
    payload = {'check_type': 'identity', 'scenario': 'success', 'idempotency_key': 'same-key'}
    first = c.post(f"/api/v1/requests/{item['id']}/mock-checks", json=payload)
    assert first.status_code == 200, first.text
    assert c.post(f"/api/v1/requests/{second['id']}/mock-checks", json=payload).status_code == 409
    from backend.app.mocks.service import run_mock_check
    from backend.app.mocks.schemas import MockRun
    from backend.app.models import MockCheck
    barrier = Barrier(2)
    def run(_):
        with Session(engine) as db:
            actor = db.scalar(select(User).where(User.email == 'izin@test.id'))
            request = db.get(Request, item['id']); barrier.wait(timeout=10)
            check = run_mock_check(db, actor, request, MockRun(**{**payload, 'idempotency_key': 'parallel-key'}))
            db.commit(); return check.id
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(run, range(2))); assert result[0] == result[1]
    with Session(engine) as db: assert db.query(MockCheck).filter_by(idempotency_key='parallel-key').count() == 1
