import pytest
from sqlalchemy import select, event
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.tests.test_parallel_decisions import prepared, decision
from backend.tests.conftest import login, register
from backend.app.models import User, Agency, Request, RequestEvent


def finalize(c, item):
    for index, email in enumerate(['izin@test.id', 'pajak@test.id']):
        login(c, email)
        item = decision(c, item, item['workflows'][index], 'processing').json()
        item = decision(c, item, item['workflows'][index], 'approved').json()
    return item


def test_result_snapshot_access_and_immutable_names(appdb):
    c, engine, item, ids = prepared(appdb)
    url = f"/api/v1/requests/{item['id']}/result"
    assert c.get(url).status_code == 404
    item = finalize(c, item)
    login(c)
    response = c.get(url); assert response.status_code == 200, response.text
    result = response.json()
    assert result['number'].startswith('SGWA-DEMO-')
    assert result['snapshot']['status'] == 'approved'
    assert len(result['snapshot']['agency_decisions']) == 2
    assert result['snapshot']['finalized_at'] and not result['snapshot']['converted']
    with Session(engine) as db:
        from backend.app.results.service import ensure_result_document
        from backend.app.models import ResultDocument
        stored = ensure_result_document(db, db.get(Request, item['id']))
        assert stored.id == result['id'] and db.query(ResultDocument).count() == 1
        db.get(User, item['citizen_id']).name = 'Nama baru'
        db.get(Agency, ids[0]).name = 'Dinas baru'; db.commit()
    assert c.get(url).json() == result
    register(c, 'another@test.id'); login(c, 'another@test.id')
    assert c.get(url).status_code == 404
    with Session(engine) as db:
        actor = db.scalar(select(User).where(User.email == 'izin@test.id'))
        actor.agency_id = None; db.commit()
    login(c, 'izin@test.id'); assert c.get(url).status_code == 404


def test_legacy_rejected_backfill_does_not_invent_timeline(appdb):
    c, engine, item, ids = prepared(appdb)
    from backend.app.results.service import ensure_result_document
    from scripts.backfill_results import backfill
    with Session(engine) as db:
        request = db.get(Request, item['id']); request.status = 'rejected'
        db.query(RequestEvent).delete(); db.commit()
    assert backfill(engine) == 1 and backfill(engine) == 0
    with Session(engine) as db:
        request = db.get(Request, item['id'])
        result = ensure_result_document(db, request, converted=True); db.commit()
        assert result.snapshot['finalized_at'] is None and result.snapshot['notes'] is None
        assert result.snapshot['converted'] and result.snapshot['status'] == 'rejected'
        assert ensure_result_document(db, request, converted=True).id == result.id


def test_result_insert_failure_rolls_back_final_decision(appdb):
    c, engine, item, ids = prepared(appdb)
    login(c, 'izin@test.id')
    item = decision(c, item, item['workflows'][0], 'processing').json()
    item = decision(c, item, item['workflows'][0], 'approved').json()
    login(c, 'pajak@test.id'); item = decision(c, item, item['workflows'][1], 'processing').json()
    def fail(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith('INSERT INTO RESULT_DOCUMENTS'): raise SQLAlchemyError('injected result failure')
    event.listen(engine, 'before_cursor_execute', fail)
    try:
        assert decision(c, item, item['workflows'][1], 'approved').status_code == 503
    finally: event.remove(engine, 'before_cursor_execute', fail)
    current = c.get(f"/api/v1/requests/{item['id']}").json()
    assert current['version'] == item['version'] and current['status'] == 'processing'
    assert current['workflows'][1]['status'] == 'processing'


def test_admin_rejection_generates_result(appdb):
    c, engine, item, ids = prepared(appdb)
    login(c, 'izin@test.id')
    item = decision(c, item, item['workflows'][0], 'escalated').json()
    login(c, 'admin@test.id')
    response = c.patch(f"/api/v1/requests/{item['id']}/status", json={'version': item['version'], 'status': 'rejected', 'note': 'Permohonan ditolak setelah review'})
    assert response.status_code == 200, response.text
    result = c.get(f"/api/v1/requests/{item['id']}/result").json()
    assert result['snapshot']['status'] == 'rejected'
    assert result['snapshot']['notes'] == 'Permohonan ditolak setelah review'
