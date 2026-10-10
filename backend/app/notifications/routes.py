from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.auth.dependencies import get_current_user
from backend.app.models import User, Notification, utcnow
from backend.app.notifications.service import notification_out
from backend.app.notifications.schemas import UnreadCount

router = APIRouter(prefix='/notifications', tags=['Notifikasi'])


@router.get('')
def listing(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    query = select(Notification).where(Notification.user_id == actor.id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Notification.id.desc()).offset((page-1)*page_size).limit(page_size))
    return {'items': [notification_out(db, actor, row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


@router.get('/unread-count', response_model=UnreadCount)
def count(actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    return {'count': db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == actor.id, Notification.read_at.is_(None)))}


@router.post('/read-all')
def read_all(actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    db.execute(update(Notification).where(Notification.user_id == actor.id, Notification.read_at.is_(None)).values(read_at=utcnow())); db.commit()
    return {'ok': True}


@router.patch('/{notification_id}/read')
def read(notification_id: int, actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == actor.id).with_for_update())
    if not row: raise HTTPException(404, 'Notifikasi tidak ditemukan.')
    if row.read_at is None: row.read_at = utcnow()
    db.commit()
    return notification_out(db, actor, row)
