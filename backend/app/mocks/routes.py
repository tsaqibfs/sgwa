from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User, MockCheck
from backend.app.auth.dependencies import require_role
from backend.app.requests.service import get_request
from backend.app.mocks.schemas import MockRun
from backend.app.mocks.service import run_mock_check, mock_out

router = APIRouter(prefix='/requests', tags=['Simulasi API'])


@router.get('/{request_id}/mock-checks')
def history(request_id: int, actor: User = Depends(require_role('staff', 'admin')), db: Session = Depends(get_session)):
    item = get_request(db, actor, request_id)
    return [mock_out(row) for row in db.scalars(select(MockCheck).where(MockCheck.request_id == item.id).order_by(MockCheck.id.desc()))]


@router.post('/{request_id}/mock-checks')
def run(request_id: int, payload: MockRun, actor: User = Depends(require_role('staff', 'admin')), db: Session = Depends(get_session)):
    item = get_request(db, actor, request_id)
    check = run_mock_check(db, actor, item, payload); db.commit()
    return mock_out(check)
