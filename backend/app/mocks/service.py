from fastapi import HTTPException
from sqlalchemy import select
from backend.app.models import User, Request, MockCheck
from backend.app.requests.service import scoped_query, iso
from backend.app.audit.service import record

FIXTURES = {
    'identity': {'fixture': 'IDENTITY-DEMO-001', 'subject': 'Identitas sintetis'},
    'permit_completeness': {'fixture': 'PERMIT-DEMO-001', 'subject': 'Kelengkapan izin sintetis'},
    'general_service': {'fixture': 'SERVICE-DEMO-001', 'subject': 'Layanan sintetis'},
}
MESSAGES = {'success': 'Data simulasi cocok.', 'mismatch': 'Data simulasi tidak cocok; perlu pemeriksaan petugas.', 'unavailable': 'Sumber simulasi sedang tidak tersedia.'}


def run_mock_check(db, actor, item, payload):
    # Actor mutex serializes retries, including reuse against different requests.
    actor = db.scalar(select(User).where(User.id == actor.id).with_for_update().execution_options(populate_existing=True))
    if not actor.active: raise HTTPException(401, 'Sesi berakhir.')
    if actor.role not in ('staff', 'admin'): raise HTTPException(403, 'Pemeriksaan hanya untuk petugas.')
    item = db.scalar(scoped_query(actor).where(Request.id == item.id).with_for_update().execution_options(populate_existing=True))
    if not item: raise HTTPException(404, 'Permohonan tidak ditemukan.')
    existing = db.scalar(select(MockCheck).where(MockCheck.actor_id == actor.id, MockCheck.idempotency_key == payload.idempotency_key).with_for_update())
    if existing:
        if (existing.request_id, existing.check_type, existing.outcome) != (item.id, payload.check_type, payload.scenario): raise HTTPException(409, 'Kunci pemeriksaan telah dipakai untuk input berbeda.')
        return existing
    check = MockCheck(request_id=item.id, actor_id=actor.id, check_type=payload.check_type, outcome=payload.scenario, idempotency_key=payload.idempotency_key, payload={'simulation': True, **FIXTURES[payload.check_type], 'message': MESSAGES[payload.scenario]})
    db.add(check); db.flush()
    record(db, actor.id, 'mock.checked', 'request', item.id, {'check_id': check.id, 'check_type': check.check_type, 'outcome': check.outcome, 'simulation': True})
    return check


def mock_out(check):
    return {'id': check.id, 'request_id': check.request_id, 'actor_id': check.actor_id, 'check_type': check.check_type, 'outcome': check.outcome, 'checked_at': iso(check.checked_at), 'payload': check.payload, 'simulation': True}
