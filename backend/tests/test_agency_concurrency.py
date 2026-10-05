from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from sqlalchemy import event,select,update,text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from backend.tests.conftest import register,login,seed_actor
from backend.app.models import Agency,User,Request
from backend.app.requests.schemas import RequestCreate
from backend.app.requests.service import submit_request
from backend.app.workflow.service import reroute_request


@pytest.mark.parametrize('mode',['submit','reroute'])
def test_agency_cannot_be_deactivated_between_check_and_route_commit(appdb,mode):
    client,engine,app=appdb
    with Session(engine) as db:
        agency=Agency(code='dukcapil',name='Dukcapil');db.add(agency);db.commit();agency_id=agency.id
    register(client);actor_id=login(client).json()['user']['id'];request_id=None
    if mode=='reroute':
        request_id=client.post('/api/v1/requests',json={'title':'zzzzz qqqqq','description':'zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq'}).json()['id']
        actor_id=seed_actor(engine,'admin','admin@example.com')
    ready,release=Event(),Event()
    def route():
        with Session(engine,expire_on_commit=False) as db:
            def pause_flush(session,*args):
                if any(isinstance(item,Request) for item in session.new):
                    ready.set();assert release.wait(10)
            def pause_update(state):
                if state.is_update and getattr(state.statement.table,'name','')=='requests':
                    ready.set();assert release.wait(10)
            event.listen(db,'before_flush',pause_flush) if mode=='submit' else event.listen(db,'do_orm_execute',pause_update)
            actor=db.get(User,actor_id)
            if mode=='submit':
                return submit_request(db,actor,RequestCreate(title='Pengurusan KTP',description='Saya ingin mengurus KTP dan kartu keluarga penduduk di Dukcapil.'),app.state.classifier).status
            return reroute_request(db,actor,request_id,1,agency_id,'Ditinjau untuk Dukcapil').status
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(route)
        try:
            assert ready.wait(10)
            code=None
            with Session(engine) as db:
                db.execute(text('SET innodb_lock_wait_timeout=1'))
                try:
                    db.execute(update(Agency).where(Agency.id==agency_id).values(active=False));db.commit()
                except OperationalError as exc:
                    code=exc.orig.args[0];db.rollback()
            assert code==1205, 'Deactivation committed during an unfinished route transaction'
        finally:
            release.set()
        assert future.result(timeout=10)=='pending'
