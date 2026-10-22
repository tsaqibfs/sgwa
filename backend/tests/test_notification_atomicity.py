import pytest
from sqlalchemy import event, select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.app.models import Request, RequestWorkflow, RequestEvent, AuditLog
from backend.tests.test_parallel_decisions import prepared


def test_notification_failure_rolls_back_workflow(appdb):
    c, engine, item, ids = prepared(appdb)
    from backend.app.models import User
    from backend.app.workflow.tasks import decide_task
    def fail(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith('INSERT INTO NOTIFICATIONS'):
            raise SQLAlchemyError('injected notification failure')
    with Session(engine) as db:
        actor = db.scalar(select(User).where(User.email == 'izin@test.id'))
        counts = [db.scalar(select(func.count()).select_from(m)) for m in (RequestEvent, AuditLog)]
        event.listen(engine, 'before_cursor_execute', fail)
        try:
            with pytest.raises(SQLAlchemyError):
                decide_task(db, actor, item['id'], item['workflows'][0]['id'], item['version'], 1, 'processing', '')
            db.rollback()
        finally: event.remove(engine, 'before_cursor_execute', fail)
        assert db.get(Request, item['id']).version == 1
        assert db.get(RequestWorkflow, item['workflows'][0]['id']).version == 1
        assert counts == [db.scalar(select(func.count()).select_from(m)) for m in (RequestEvent, AuditLog)]


def test_notification_failure_rolls_back_submission(appdb):
    c, engine, item, ids = prepared(appdb)
    models = (Request, RequestWorkflow, RequestEvent, AuditLog)
    with Session(engine) as db: counts = [db.scalar(select(func.count()).select_from(m)) for m in models]
    def fail(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith('INSERT INTO NOTIFICATIONS'): raise SQLAlchemyError('injected')
    event.listen(engine, 'before_cursor_execute', fail)
    try:
        assert c.post('/api/v1/requests', json={'title': 'Perizinan kedua', 'description': 'Saya ingin mengurus perizinan usaha dan pajak atas usaha tersebut.'}).status_code == 503
    finally: event.remove(engine, 'before_cursor_execute', fail)
    with Session(engine) as db: assert counts == [db.scalar(select(func.count()).select_from(m)) for m in models]


def test_concurrent_decisions_create_one_event_notification(appdb):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from backend.app.models import User, Notification
    from backend.app.workflow.tasks import decide_task
    c, engine, item, ids = prepared(appdb)
    barrier = Barrier(2)
    def act(index):
        with Session(engine) as db:
            actor = db.scalar(select(User).where(User.email == ('izin@test.id' if index == 0 else 'pajak@test.id')))
            barrier.wait(timeout=10)
            try:
                decide_task(db, actor, item['id'], item['workflows'][index]['id'], 1, 1, 'processing', '')
                return 200
            except HTTPException as exc: db.rollback(); return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool: assert sorted(pool.map(act, [0, 1])) == [200, 409]
    with Session(engine) as db:
        assert db.query(Notification).filter_by(kind='task_updated').count() == 1
