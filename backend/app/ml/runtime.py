"""Resolve one validated immutable classifier snapshot from the MySQL pointer."""
from fastapi import Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import MLActiveModel,MLModelVersion
from backend.app.ml.registry import validated_version
from backend.app.ml.classifier import Classifier,ModelUnavailable


def active_classifier(db: Session,app) -> Classifier:
    pointer=db.scalar(select(MLActiveModel).where(MLActiveModel.id==1).execution_options(populate_existing=True))
    if not pointer or not pointer.model_version_id:raise HTTPException(503,'Model belum aktif. Jalankan bootstrap ML.')
    row=db.get(MLModelVersion,pointer.model_version_id)
    try:
        directory,info,report=validated_version(row)
        cache=getattr(app.state,'ml_classifier_cache',{})
        classifier=cache.get(row.id)
        if classifier is None:
            classifier=Classifier(directory)
            cache={row.id:classifier};app.state.ml_classifier_cache=cache
        return classifier
    except (ValueError,OSError,KeyError,TypeError,ModelUnavailable) as exc:
        app.state.ml_classifier_cache={}
        raise HTTPException(503,'Artefak model aktif hilang atau tidak valid. Admin perlu memulihkan atau rollback.') from exc


def get_classifier(request: Request,db: Session=Depends(get_session)) -> Classifier:
    return active_classifier(db,request.app)
