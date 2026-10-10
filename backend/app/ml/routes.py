from fastapi import APIRouter,Depends,Request,HTTPException,Query
from sqlalchemy import select,func
from typing import Literal
from sqlalchemy.orm import Session
from backend.app.models import User,Agency
from backend.app.db import get_session
from backend.app.auth.dependencies import require_role
from backend.app.models import MLFeedback
from backend.app.ml.schemas import FeedbackCreate,FeedbackReview
from backend.app.ml.feedback import create_feedback,review_feedback,feedback_out

router=APIRouter(prefix='/ml',tags=['Model ML'])


def model(request: Request):
    classifier=request.app.state.classifier
    if classifier is None:
        raise HTTPException(503,'Model belum tersedia. Jalankan training dan restart backend.')
    return classifier


@router.get('/metadata')
def metadata(request: Request,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    info=model(request).metadata()
    agencies=db.scalars(select(Agency).where(Agency.active.is_(True))).all()
    return {**info,'unsupported_agencies':[a.code for a in agencies if a.code not in info['classes']]}


@router.get('/evaluation')
def evaluation(request: Request,actor: User=Depends(require_role('admin'))):
    return model(request).report


@router.get('/feedback')
def feedback_list(status:Literal['pending','verified','rejected','superseded']|None=None,provenance:Literal['synthetic_demo','real']|None=None,
                  request_id:int|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),
                  actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    query=select(MLFeedback)
    if status:query=query.where(MLFeedback.status==status)
    if provenance:query=query.where(MLFeedback.provenance==provenance)
    if request_id is not None:query=query.where(MLFeedback.request_id==request_id)
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    rows=db.scalars(query.order_by(MLFeedback.id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {'items':[feedback_out(db,row) for row in rows],'total':total,'page':page,'page_size':page_size}


@router.get('/feedback/{feedback_id}')
def feedback_detail(feedback_id:int,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    row=db.get(MLFeedback,feedback_id)
    if not row:raise HTTPException(404,'Koreksi tidak ditemukan.')
    return feedback_out(db,row)


@router.post('/requests/{request_id}/feedback',status_code=201)
def feedback_create(request_id:int,payload:FeedbackCreate,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return feedback_out(db,create_feedback(db,actor,request_id,payload))


@router.post('/feedback/{feedback_id}/review')
def feedback_review(feedback_id:int,payload:FeedbackReview,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return feedback_out(db,review_feedback(db,actor,feedback_id,payload))
