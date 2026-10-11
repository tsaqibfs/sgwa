import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.models import Agency,Request,MLFeedback,MLFeedbackHead,MLModelVersion,MLActiveModel
from backend.tests.conftest import seed_actor


def test_snapshot_current_verified_only_and_stable(appdb):
    assert importlib.util.find_spec('backend.app.ml.feedback_export'), 'Feedback snapshot missing'
    from backend.app.ml.feedback_export import snapshot_feedback
    _,engine,_=appdb
    actor=seed_actor(engine,'admin','export@test.id')
    with Session(engine) as db:
        db.add(Agency(code='dukcapil',name='Dukcapil'));db.flush()
        for n,status in enumerate(('verified','pending','rejected','superseded'),1):
            req=Request(reference=f'EXPORT-{n}',citizen_id=actor,title='Title',description='Description');db.add(req);db.flush()
            feedback=MLFeedback(request_id=req.id,revision=1,original_text='original',original_prediction={},training_text=f'KTP keluarga varian {n}',text_hash='a'*64,corrected_code='dukcapil',provenance='synthetic_demo',reason='reason',status=status,created_by=actor,idempotency_key=str(n),payload_hash='b'*64)
            db.add(feedback);db.flush();db.add(MLFeedbackHead(request_id=req.id,revision=1,current_feedback_id=feedback.id))
        db.commit()
        snapshot=snapshot_feedback(db)
        assert len(snapshot['entries'])==1 and snapshot['entries'][0]['request_id']==1
        assert snapshot_feedback(db)==snapshot


def test_register_candidate_rejects_incomplete_and_never_activates(appdb,tmp_path):
    assert importlib.util.find_spec('backend.app.ml.registry'), 'Model registry missing'
    from backend.app.ml.registry import register_candidate
    _,engine,_=appdb
    with Session(engine) as db:
        with pytest.raises((ValueError,FileNotFoundError)):register_candidate(db,tmp_path,None)
        assert db.scalar(select(func.count()).select_from(MLModelVersion))==0
        assert db.scalar(select(MLActiveModel.model_version_id)) is None


def test_register_candidate_repeat_is_idempotent(appdb,tmp_path,monkeypatch):
    assert importlib.util.find_spec('backend.app.ml.registry'), 'Model registry missing'
    from ml.train import train
    from backend.app.ml.registry import register_candidate
    from backend.app.config import get_settings
    _,engine,_=appdb
    get_settings().model_dir=tmp_path
    stage=tmp_path/'stage';report=train(Path('ml/data/requests.csv'),stage,holdout_path=Path('ml/data/holdout.json'))
    directory=tmp_path/'versions'/report['model_version'];directory.parent.mkdir();stage.rename(directory)
    with Session(engine) as db:
        first=register_candidate(db,directory,None);db.commit()
        assert register_candidate(db,directory,None).id==first.id
        assert db.scalar(select(func.count()).select_from(MLModelVersion))==1
        assert db.scalar(select(MLActiveModel.model_version_id)) is None


def test_registry_tolerates_mysql_json_float_roundtrip_but_rejects_changed_scores(appdb,tmp_path):
    import json,hashlib
    from ml.train import train
    from backend.app.ml.registry import register_candidate,validated_version
    from backend.app.config import get_settings
    _,engine,_=appdb;get_settings().model_dir=tmp_path
    stage=tmp_path/'stage';report=train(Path('ml/data/requests.csv'),stage,holdout_path=Path('ml/data/holdout.json'))
    report['cross_validation']['folds'][1]['macro_f1']=0.45417268445839876
    evaluation=stage/'evaluation.json';evaluation.write_text(json.dumps(report),encoding='utf-8')
    metadata=stage/'metadata.json';info=json.loads(metadata.read_text());info['artifact_hashes']['evaluation.json']=hashlib.sha256(evaluation.read_bytes()).hexdigest();metadata.write_text(json.dumps(info),encoding='utf-8')
    directory=tmp_path/'versions'/report['model_version'];directory.parent.mkdir();stage.rename(directory)
    with Session(engine) as db:
        row=register_candidate(db,directory,None);db.commit();db.expire_all()
        validated_version(db.get(MLModelVersion,row.id))
        changed=json.loads(json.dumps(row.evaluation_json));changed['macro_f1']+=0.001;row.evaluation_json=changed;db.commit()
        with pytest.raises(ValueError,match='Registry'):validated_version(row)
