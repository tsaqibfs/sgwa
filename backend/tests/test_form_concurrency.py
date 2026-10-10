from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models import User
from backend.app.forms.routes import publish,edit
from backend.app.forms.schemas import Publish,DraftUpdate
from backend.tests.test_service_forms import form_setup,FIELDS


def competing(engine,form_id,operation):
    barrier=Barrier(2)
    def invoke(i):
        with Session(engine,expire_on_commit=False) as db:
            actor=db.query(User).filter_by(email='admin@forms.id').one()
            barrier.wait(timeout=10)
            try:
                operation(form_id,actor,db,i)
                return 200
            except HTTPException as exc:
                db.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:
        return sorted(pool.map(invoke,(1,2)))


def test_only_one_concurrent_publication_succeeds(appdb):
    _,engine,_,form=form_setup(appdb)
    assert competing(engine,form['id'],lambda id,actor,db,i:publish(id,Publish(expected_version=1),actor,db))==[200,409]


def test_draft_updates_reject_lost_update(appdb):
    _,engine,_,form=form_setup(appdb)
    assert competing(engine,form['id'],lambda id,actor,db,i:edit(id,DraftUpdate(expected_version=1,title=f'Updated {i}',fields=FIELDS),actor,db))==[200,409]
