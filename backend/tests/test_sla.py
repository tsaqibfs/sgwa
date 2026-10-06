from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.models import RequestWorkflow,Request,RequestEvent,utcnow
from backend.tests.test_parallel_decisions import prepared
from backend.tests.conftest import login


def test_deadline_boundary_snapshot_and_idempotent_workers(appdb):
    from backend.app.sla.service import escalate_overdue
    c,engine,item,ids=prepared(appdb);now=utcnow().replace(microsecond=0)
    with Session(engine) as db:
        tasks=db.scalars(select(RequestWorkflow).order_by(RequestWorkflow.id)).all()
        tasks[0].due_at=now;tasks[1].due_at=now+timedelta(days=5);db.commit()
    login(c,'admin@test.id');assert c.patch(f'/api/v1/agencies/{ids[0]}',json={'sla_days':1}).status_code==200
    with Session(engine) as db:
        assert db.get(RequestWorkflow,item['workflows'][0]['id']).due_at==now
        assert escalate_overdue(db,now)==0
    def scan():
        with Session(engine) as db:return escalate_overdue(db,now+timedelta(seconds=1))
    with ThreadPoolExecutor(max_workers=2) as pool:assert sum(pool.map(lambda _:scan(),range(2)))==1
    with Session(engine) as db:
        assert db.get(Request,item['id']).status=='escalated'
        assert db.scalar(select(func.count()).select_from(RequestEvent).where(RequestEvent.event_type=='sla_escalated'))==1
        assert escalate_overdue(db,now+timedelta(days=10))==0
    dashboard=c.get('/api/v1/dashboard').json();assert dashboard['overdue_count']==1
    assert dashboard['average_completed_hours'] is None


def test_terminal_requests_and_completed_tasks_are_not_escalated(appdb):
    from backend.app.sla.service import escalate_overdue
    c,engine,item,ids=prepared(appdb);now=utcnow().replace(microsecond=0)
    with Session(engine) as db:
        parent=db.get(Request,item['id']);parent.status='approved'
        for task in db.scalars(select(RequestWorkflow)):task.due_at=now-timedelta(days=2)
        db.commit()
        assert escalate_overdue(db,now)==0
        assert parent.status=='approved'
