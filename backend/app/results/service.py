import uuid
from sqlalchemy import select
from backend.app.models import Request, ResultDocument, RequestEvent, RequestWorkflow, Agency, User
from backend.app.requests.service import iso
from backend.app.results.schemas import ResultOut


def ensure_result_document(db, item, converted=False):
    """Lock parent and snapshot the recorded decision in the caller's transaction."""
    db.flush()
    item = db.scalar(select(Request).where(Request.id == item.id).with_for_update().execution_options(populate_existing=True))
    if item.status not in ('approved', 'rejected'): return None
    existing = db.scalar(select(ResultDocument).where(ResultDocument.request_id == item.id).with_for_update())
    if existing: return existing
    final = db.scalar(select(RequestEvent).where(RequestEvent.request_id == item.id, RequestEvent.to_status == item.status).order_by(RequestEvent.id.desc()).limit(1))
    owner = db.get(User, item.citizen_id)
    decisions = [{'agency_id': task.agency_id, 'agency_name': name, 'status': task.status, 'note': task.decision_note or None, 'completed_at': iso(task.completed_at)} for task, name in db.execute(select(RequestWorkflow, Agency.name).join(Agency, Agency.id == RequestWorkflow.agency_id).where(RequestWorkflow.request_id == item.id).order_by(RequestWorkflow.agency_id))]
    number = 'SGWA-DEMO-' + str(uuid.uuid4()).upper()
    result = ResultDocument(request_id=item.id, number=number, snapshot={'number': number, 'reference': item.reference, 'owner_name': owner.name, 'title': item.title, 'status': item.status, 'finalized_at': iso(final.created_at) if final else None, 'notes': final.note if final else None, 'agency_decisions': decisions, 'converted': converted})
    db.add(result); db.flush()
    return result


def result_out(result):
    return ResultOut(id=result.id, number=result.number, request_id=result.request_id, snapshot=result.snapshot).model_dump()
