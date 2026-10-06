import asyncio
import jwt
from sqlalchemy.orm import Session
from backend.app.models import User,Request
from backend.tests.test_parallel_decisions import prepared
from backend.tests.conftest import register,login
from backend.app.auth.service import make_session
from backend.app.config import get_settings


def test_scoped_revision_and_stream_reassignment(appdb):
    from backend.app.live.service import scoped_revision,iter_events
    c,engine,item,ids=prepared(appdb)
    with Session(engine) as db:
        staff=db.query(User).filter_by(email='izin@test.id').one();staff_id=staff.id
        citizen=db.query(User).filter_by(email='warga@example.com').one();citizen_id=citizen.id
    register(c,'other@test.id');other=login(c,'other@test.id').json()['user']['id']
    with Session(engine) as db:
        before=scoped_revision(db,db.get(User,other));owner_before=scoped_revision(db,db.get(User,citizen_id))
        db.get(Request,item['id']).version+=1;db.commit()
        assert scoped_revision(db,db.get(User,other))==before
        assert scoped_revision(db,db.get(User,citizen_id))!=owner_before
    token,_=make_session(staff_id)
    async def check():
        stream=iter_events(engine,token,poll_seconds=0)
        initial=await anext(stream);assert 'event: changed' in initial
        assert item['title'] not in initial and 'agency_id' not in initial and token not in initial
        with Session(engine) as db:db.get(User,staff_id).agency_id=ids[1];db.commit()
        assert 'event: session-invalid' in await anext(stream)
        try:await anext(stream)
        except StopAsyncIteration:pass
        else:assert False,'Stream must close after scope change'
        expired=iter_events(engine,jwt.encode({'sub':str(staff_id),'exp':1,'kind':'session'},get_settings().jwt_secret,algorithm='HS256'),poll_seconds=0)
        assert 'session-invalid' in await anext(expired)
        await expired.aclose()
    asyncio.run(check())
