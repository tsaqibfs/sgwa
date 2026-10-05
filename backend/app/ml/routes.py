from fastapi import APIRouter,Depends,Request,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import User,Agency
from backend.app.db import get_session
from backend.app.auth.dependencies import require_role

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
