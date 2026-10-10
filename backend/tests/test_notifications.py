from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.tests.test_parallel_decisions import prepared, decision
from backend.tests.conftest import login, seed_actor
from backend.app.models import User, Request


def test_notifications_recipients_read_scope_and_reassignment(appdb):
    c, engine, item, ids = prepared(appdb)
    assert c.get('/api/v1/notifications/unread-count').json() == {'count': 1}
    own = c.get('/api/v1/notifications?page_size=1').json()
    assert own['total'] == 1 and own['items'][0]['can_open_request']
    notification = own['items'][0]['id']
    assert c.patch(f'/api/v1/notifications/{notification}/read').status_code == 200
    assert c.patch(f'/api/v1/notifications/{notification}/read').status_code == 200
    assert c.get('/api/v1/notifications/unread-count').json()['count'] == 0
    login(c, 'izin@test.id')
    assert c.patch(f'/api/v1/notifications/{notification}/read').status_code == 404
    item = decision(c, item, item['workflows'][0], 'processing').json()
    item = decision(c, item, item['workflows'][0], 'escalated').json()
    login(c, 'admin@test.id')
    assert c.get('/api/v1/notifications/unread-count').json()['count'] == 1
    item = c.post(f"/api/v1/requests/{item['id']}/review-route", json={'version': item['version'], 'agency_ids': [ids[1]], 'note': 'Alihkan tugas'}).json()
    login(c, 'pajak@test.id')
    assert c.get('/api/v1/notifications').json()['total'] == 1
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == 'pajak@test.id'))
        user.agency_id = ids[0]; db.commit()
    notices = c.get('/api/v1/notifications').json()['items']
    assert all(not n['can_open_request'] and n['title'] == 'Pembaruan layanan' for n in notices)
    assert c.post('/api/v1/notifications/read-all').status_code == 200
    assert c.get('/api/v1/notifications/unread-count').json()['count'] == 0


def test_submission_notifies_existing_staff_and_final_citizen(appdb):
    c, engine, first, ids = prepared(appdb)
    item = c.post('/api/v1/requests', json={'title': 'Perizinan ketiga', 'description': 'Saya ingin mengurus perizinan usaha dan pajak atas usaha tersebut.'}).json()
    for index, email in enumerate(['izin@test.id', 'pajak@test.id']):
        login(c, email)
        assert c.get('/api/v1/notifications').json()['items'][0]['request_id'] == item['id']
        item = decision(c, item, item['workflows'][index], 'processing').json()
        item = decision(c, item, item['workflows'][index], 'approved').json()
    login(c)
    assert item['status'] == 'approved'
    assert c.get('/api/v1/notifications').json()['total'] == 6


def test_notifications_deduplicate_inactive_and_scoped_sse(appdb):
    c, engine, item, ids = prepared(appdb)
    from backend.app.notifications.service import notify_request_event
    from backend.app.models import Notification
    from backend.app.live.service import scoped_revision
    inactive = seed_actor(engine, 'admin', 'inactive@test.id')
    with Session(engine) as db:
        db.get(User, inactive).active = False; db.commit()
        actor = db.scalar(select(User).where(User.role == 'citizen'))
        other = db.scalar(select(User).where(User.email == 'admin@test.id'))
        before = scoped_revision(db, actor); other_before = scoped_revision(db, other)
        request = db.get(Request, item['id'])
        for _ in range(2): notify_request_event(db, request, 'test-event', 'status_changed', [])
        db.commit()
        assert db.query(Notification).filter_by(event_key='test-event').count() == 1
        assert db.query(Notification).filter_by(user_id=inactive).count() == 0
        assert scoped_revision(db, actor) != before
        assert scoped_revision(db, other) == other_before
        notice = db.scalar(select(Notification).where(Notification.event_key == 'test-event'))
        before = scoped_revision(db, actor); notice.read_at = request.created_at; db.commit()
        assert scoped_revision(db, actor) != before
