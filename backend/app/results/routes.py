from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User, ResultDocument
from backend.app.auth.dependencies import get_current_user
from backend.app.requests.service import get_request
from backend.app.results.service import result_out
from backend.app.results.schemas import ResultOut

router = APIRouter(prefix='/requests', tags=['Bukti hasil'])


@router.get('/{request_id}/result', response_model=ResultOut)
def detail(request_id: int, actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    item = get_request(db, actor, request_id)
    document = db.scalar(select(ResultDocument).where(ResultDocument.request_id == item.id))
    if item.status not in ('approved', 'rejected') or not document: raise HTTPException(404, 'Bukti hasil belum tersedia.')
    return result_out(document)
