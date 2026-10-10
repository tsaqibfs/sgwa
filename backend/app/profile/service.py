from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import User
from backend.app.auth.service import hash_password, verify_password
from backend.app.audit.service import record


def locked_actor(db: Session, actor: User) -> User:
    version = actor.session_version
    current = db.scalar(select(User).where(User.id == actor.id).with_for_update().execution_options(populate_existing=True))
    if not current or not current.active or current.session_version != version:
        raise HTTPException(401, 'Sesi berakhir. Silakan masuk kembali.')
    return current


def update_profile(db: Session, actor: User, payload) -> User:
    actor = locked_actor(db, actor)
    fields = payload.model_dump(exclude_unset=True)
    for name, value in fields.items():
        setattr(actor, name, value or None if name != 'name' else value)
    record(db, actor.id, 'profile.updated', 'user', actor.id, {'fields': sorted(fields)})
    db.commit()
    return actor


def change_password(db: Session, actor: User, payload) -> None:
    actor = locked_actor(db, actor)
    if not verify_password(payload.current_password, actor.password_hash):
        raise HTTPException(400, 'Password saat ini tidak sesuai.')
    if payload.current_password == payload.new_password:
        raise HTTPException(422, 'Password baru harus berbeda.')
    actor.password_hash = hash_password(payload.new_password)
    actor.session_version += 1
    record(db, actor.id, 'profile.password_changed', 'user', actor.id, {'sessions_revoked': True})
    db.commit()
