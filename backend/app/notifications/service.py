from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from backend.app.models import Notification, User, Request
from backend.app.requests.service import scoped_query, iso


def notify_request_event(db, item, event_key, kind, assigned_agency_ids):
    """Participate in the caller's transaction; do not commit."""
    recipients = [User.id == item.citizen_id]
    if kind in ('submitted', 'rerouted') and item.status != 'escalated':
        recipients.append((User.role == 'staff') & User.agency_id.in_(assigned_agency_ids))
    if item.status == 'escalated': recipients.append(User.role == 'admin')
    title = {'submitted': 'Permohonan diterima', 'rerouted': 'Arah layanan diperbarui'}.get(kind, 'Status layanan diperbarui')
    for user_id in db.scalars(select(User.id).where(User.active.is_(True), or_(*recipients)).order_by(User.id)):
        try:
            with db.begin_nested():
                db.add(Notification(user_id=user_id, event_key=event_key, kind=kind, title=title, request_id=item.id))
                db.flush()
        except IntegrityError as exc:
            if getattr(exc.orig, 'args', (None,))[0] != 1062: raise
            if not db.scalar(select(Notification.id).where(Notification.user_id == user_id, Notification.event_key == event_key).with_for_update()): raise


def notification_out(db, actor, notice):
    allowed = bool(notice.request_id and db.scalar(scoped_query(actor).where(Request.id == notice.request_id)))
    return {'id': notice.id, 'kind': notice.kind, 'title': notice.title if allowed else 'Pembaruan layanan', 'request_id': notice.request_id if allowed else None, 'can_open_request': allowed, 'created_at': iso(notice.created_at), 'read_at': iso(notice.read_at)}
