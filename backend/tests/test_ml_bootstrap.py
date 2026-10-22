import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.models import MLActiveModel,MLModelVersion,MLActivation
from backend.tests.conftest import seed_actor


def test_bootstrap_first_then_preserves_admin_active_and_candidate(appdb,tmp_path):
    assert importlib.util.find_spec('scripts.bootstrap_ml'),'Bootstrap not implemented'
    from scripts.bootstrap_ml import bootstrap_ml
    from scripts.train_candidate import train_candidate
    from backend.app.ml.registry import activate_model
    from backend.app.models import User
    _,engine,_=appdb
    get_settings().model_dir=tmp_path
    actor_id=seed_actor(engine,'admin','bootstrap@test.id')
    first=bootstrap_ml()
    assert first['created'] and first['model_id'].startswith('ml25-')
    candidate=train_candidate('bootstrap@test.id')
    with Session(engine) as db:
        pointer=db.get(MLActiveModel,1)
        assert pointer.model_version_id==first['model_id']
        activate_model(db,db.get(User,actor_id),candidate,pointer.revision,'Review candidate')
        revision=db.get(MLActiveModel,1).revision
        count=db.scalar(select(func.count()).select_from(MLModelVersion))
    again=bootstrap_ml()
    assert not again['created'] and again['model_id']==candidate
    with Session(engine) as db:
        assert db.get(MLActiveModel,1).revision==revision
        assert db.scalar(select(func.count()).select_from(MLModelVersion))==count


def test_missing_active_artifacts_fails_instead_of_retraining(appdb,tmp_path):
    assert importlib.util.find_spec('scripts.bootstrap_ml'),'Bootstrap not implemented'
    from scripts.bootstrap_ml import bootstrap_ml
    _,engine,_=appdb
    get_settings().model_dir=tmp_path
    first=bootstrap_ml()
    file=tmp_path/'versions'/first['model_id']/'model.joblib';file.unlink()
    with pytest.raises(ValueError,match='aktif'):bootstrap_ml()
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(MLModelVersion))==1
        assert db.scalar(select(func.count()).select_from(MLActivation))==1
