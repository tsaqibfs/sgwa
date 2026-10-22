import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.app.models import User,Agency,Request,AuditLog,Notification
from backend.app.auth.service import session_actor
from backend.app.requests.service import scoped_query


def scoped_revision(db:Session,actor:User)->str:
    scoped=scoped_query(actor).subquery()
    requests=db.execute(select(scoped.c.id,scoped.c.version).order_by(scoped.c.id)).all()
    agencies=db.execute(select(Agency.id,Agency.name,Agency.active,Agency.sla_days).order_by(Agency.id)).all()
    audit=list(db.scalars(select(AuditLog.id).order_by(AuditLog.id))) if actor.role=='admin' else []
    notices=db.execute(select(Notification.id,Notification.read_at).where(Notification.user_id==actor.id).order_by(Notification.id)).all()
    return hashlib.sha256(json.dumps([list(map(tuple,requests)),list(map(tuple,agencies)),audit,list(map(tuple,notices))],default=str).encode()).hexdigest()


def session_snapshot(engine,token:str)->tuple[tuple,str]:
    with Session(engine) as db:
        try:
            actor=session_actor(db,token)
        except (jwt.InvalidTokenError,ValueError,KeyError):raise HTTPException(401,'Sesi berakhir. Silakan masuk kembali.')
        scope=(actor.id,actor.role,actor.agency_id)
        return scope,scoped_revision(db,actor)


async def iter_events(engine,session_token:str,poll_seconds:float=3)->AsyncIterator[str]:
    previous=None;original_scope=None;heartbeat=time.monotonic()
    while True:
        try:
            scope,revision=await asyncio.to_thread(session_snapshot,engine,session_token)
        except HTTPException:
            yield 'event: session-invalid\ndata: {}\n\n';return
        except SQLAlchemyError:
            yield 'event: unavailable\ndata: {}\n\n'
            await asyncio.sleep(max(1,poll_seconds));continue
        if original_scope is not None and scope!=original_scope:
            yield 'event: session-invalid\ndata: {}\n\n';return
        original_scope=scope
        if revision!=previous:
            yield 'event: changed\ndata: '+json.dumps({'revision':revision})+'\n\n'
            previous=revision
        elif time.monotonic()-heartbeat>=15:
            yield ': heartbeat\n\n';heartbeat=time.monotonic()
        await asyncio.sleep(poll_seconds)
