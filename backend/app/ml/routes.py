from fastapi import APIRouter,Depends,Request,HTTPException,Query
from sqlalchemy import select,func
from typing import Literal
from sqlalchemy.orm import Session
from backend.app.models import User,Agency
from backend.app.db import get_session
from backend.app.auth.dependencies import require_role
from backend.app.models import MLFeedback
from backend.app.ml.schemas import FeedbackCreate,FeedbackReview,ModelActivation
from backend.app.ml.feedback import create_feedback,review_feedback,feedback_out
from backend.app.ml.runtime import get_classifier
from backend.app.ml.registry import activate_model,validated_version,check_activation
from backend.app.models import MLModelVersion,MLActiveModel,MLActivation

router=APIRouter(prefix='/ml',tags=['Model ML'])


@router.get('/labels')
def labels(actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    from backend.app.agencies.catalog import AGENCIES
    active=set(db.scalars(select(Agency.code).where(Agency.active.is_(True))))
    return [{'code':code,'name':name,'active':code in active} for code,name in AGENCIES]


def model(request: Request):
    classifier=request.app.state.classifier
    if classifier is None:
        raise HTTPException(503,'Model belum tersedia. Jalankan training dan restart backend.')
    return classifier


@router.get('/metadata')
def metadata(request: Request,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session),classifier=Depends(get_classifier)):
    info=classifier.metadata()
    agencies=db.scalars(select(Agency).where(Agency.active.is_(True))).all()
    return {**info,'unsupported_agencies':[a.code for a in agencies if a.code not in info['classes']]}


@router.get('/evaluation')
def evaluation(request: Request,actor: User=Depends(require_role('admin')),classifier=Depends(get_classifier)):
    return classifier.report


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


@router.get('/versions')
def versions(actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    pointer=db.get(MLActiveModel,1)
    active=db.get(MLModelVersion,pointer.model_version_id) if pointer and pointer.model_version_id else None
    previously_active=set(db.scalars(select(MLActivation.model_version_id)))
    items=[]
    for row in db.scalars(select(MLModelVersion).order_by(MLModelVersion.created_at.desc(),MLModelVersion.id)):
        eligible=False;reason=row.failure_reason
        if row.state=='ready':
            try:
                _,info,report=validated_version(row)
                check_activation(active.evaluation_json if active else None,report,'activate',row.id in previously_active)
                eligible=True
            except (ValueError,OSError,KeyError,TypeError,HTTPException) as exc:
                reason=exc.detail if isinstance(exc,HTTPException) else 'Artefak tidak valid.'
        report=row.evaluation_json
        items.append({'id':row.id,'state':row.state,'created_at':row.created_at.isoformat()+'Z','macro_f1':report.get('macro_f1'),
                      'routing_policy':report.get('routing_policy'),'provenance_counts':report.get('provenance_counts'),
                      'ever_active':row.id in previously_active,'can_activate':eligible,'reason':reason,
                      'below_target':report.get('macro_f1',0)<.85})
    return {'active_model_id':pointer.model_version_id if pointer else None,'revision':pointer.revision if pointer else 0,'items':items}


@router.get('/versions/{model_id}/evaluation')
def version_evaluation(model_id:str,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    row=db.get(MLModelVersion,model_id)
    if not row:raise HTTPException(404,'Versi model tidak ditemukan.')
    try:return validated_version(row)[2]
    except (ValueError,OSError,KeyError,TypeError) as exc:raise HTTPException(422,'Artefak kandidat tidak valid.') from exc


@router.post('/versions/{model_id}/activate')
def version_activate(model_id:str,payload:ModelActivation,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return activate_model(db,actor,model_id,payload.expected_revision,payload.reason)


@router.post('/versions/{model_id}/rollback')
def version_rollback(model_id:str,payload:ModelActivation,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    return activate_model(db,actor,model_id,payload.expected_revision,payload.reason,'rollback')
