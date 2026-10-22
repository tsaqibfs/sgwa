import importlib.util
import json
from pathlib import Path
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models import MLActiveModel,MLActivation,User,Agency,Request as ServiceRequest
from backend.app.config import get_settings
from backend.tests.conftest import seed_actor,login


@pytest.fixture(scope='module')
def model_library(tmp_path_factory):
    from ml.train import train
    root=tmp_path_factory.mktemp('model-library')
    ids=[]
    for n in range(2):
        stage=root/f'stage-{n}'
        report=train(Path('ml/data/requests.csv'),stage,holdout_path=Path('ml/data/holdout.json'),feedback_manifest={'snapshot_hash':str(n)})
        target=root/'versions'/report['model_version'];target.parent.mkdir(exist_ok=True);stage.rename(target)
        ids.append(report['model_version'])
    return root,ids


@pytest.fixture
def registry_case(appdb,model_library,tmp_path):
    import shutil
    from backend.app.ml.registry import register_candidate
    client,engine,app=appdb
    app.dependency_overrides.clear()
    source,ids=model_library
    shutil.copytree(source/'versions',tmp_path/'versions')
    get_settings().model_dir=tmp_path
    actor_id=seed_actor(engine,'admin','model-admin@test.id')
    with Session(engine) as db:
        for mid in ids:register_candidate(db,tmp_path/'versions'/mid,actor_id)
        db.commit()
    login(client,'model-admin@test.id')
    return client,engine,app,ids,actor_id,tmp_path


def test_activation_requires_admin_revision_and_rollback_history(registry_case):
    client,engine,app,ids,actor,root=registry_case
    assert client.get('/api/v1/ml/metadata').status_code==503
    listing=client.get('/api/v1/ml/versions')
    assert listing.status_code==200,listing.text
    assert listing.json()['active_model_id'] is None
    activate=lambda mid,revision:client.post(f'/api/v1/ml/versions/{mid}/activate',json={'expected_revision':revision,'reason':'Model diperiksa untuk demo.'})
    assert client.post(f'/api/v1/ml/versions/{ids[1]}/rollback',json={'expected_revision':0,'reason':'Belum pernah aktif.'}).status_code==422
    assert activate(ids[0],0).status_code==200
    assert len(client.get('/api/v1/ml/metadata').json()['classes'])==25
    assert activate(ids[1],0).status_code==409
    assert activate(ids[1],1).status_code==200
    rollback=client.post(f'/api/v1/ml/versions/{ids[0]}/rollback',json={'expected_revision':2,'reason':'Kembali ke versi sebelumnya.'})
    assert rollback.status_code==200 and rollback.json()['active_model_id']==ids[0]
    with Session(engine) as db:assert db.scalar(select(func.count()).select_from(MLActivation))==3


def test_active_cache_integrity_and_invalid_paths(registry_case):
    client,engine,app,ids,actor,root=registry_case
    assert client.post(f'/api/v1/ml/versions/{ids[0]}/activate',json={'expected_revision':0,'reason':'Aktifkan model yang valid.'}).status_code==200
    assert client.get('/api/v1/ml/metadata').status_code==200
    model_path=root/'versions'/ids[0]/'model.joblib'
    model_path.write_bytes(model_path.read_bytes()+b'corrupted')
    assert client.get('/api/v1/ml/metadata').status_code==503
    from backend.app.ml.registry import artifact_directory
    from types import SimpleNamespace
    with pytest.raises(ValueError):artifact_directory(SimpleNamespace(relative_path='../outside',id=ids[0]))


def test_activation_gate_degradation_and_holdout_generation():
    from backend.app.ml import registry
    assert hasattr(registry,'check_activation'),'Activation policy missing'
    active={'macro_f1':.80,'holdout_manifest_hash':'same'}
    with pytest.raises(HTTPException):registry.check_activation(active,{'macro_f1':.779,'holdout_manifest_hash':'same'},'activate',False)
    registry.check_activation(active,{'macro_f1':.78,'holdout_manifest_hash':'same'},'activate',False)
    with pytest.raises(HTTPException):registry.check_activation(active,{'macro_f1':.95,'holdout_manifest_hash':'other'},'activate',False)
    registry.check_activation(active,{'macro_f1':.60,'holdout_manifest_hash':'same'},'rollback',True)
    with pytest.raises(HTTPException):registry.check_activation(active,{'macro_f1':.60,'holdout_manifest_hash':'same'},'rollback',False)


def test_concurrent_activation_has_one_pointer_winner(registry_case):
    from concurrent.futures import ThreadPoolExecutor
    from backend.app.ml import registry
    assert hasattr(registry,'activate_model'),'Activation missing'
    _,engine,app,ids,actor_id,root=registry_case
    def activate(mid):
        with Session(engine) as db:
            try:
                registry.activate_model(db,db.get(User,actor_id),mid,0,'Concurrent activation')
                return 200
            except HTTPException as exc:db.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:answers=list(pool.map(activate,ids))
    assert sorted(answers)==[200,409]
    with Session(engine) as db:assert db.scalar(select(func.count()).select_from(MLActivation))==1


def test_prediction_keeps_policy_snapshot_on_activation(registry_case):
    assert importlib.util.find_spec('backend.app.ml.runtime'),'Registry runtime missing'
    from backend.app.ml.runtime import active_classifier
    from backend.app.ml.registry import activate_model
    from backend.app.requests.service import submit_request
    from backend.app.requests.schemas import RequestCreate
    client,engine,app,ids,actor_id,root=registry_case
    citizen=seed_actor(engine,'citizen','snapshot-citizen@test.id')
    with Session(engine) as db:
        db.add(Agency(code='dukcapil',name='Dukcapil'));db.commit()
        activate_model(db,db.get(User,actor_id),ids[0],0,'First snapshot')
        classifier=active_classifier(db,app)
        activate_model(db,db.get(User,actor_id),ids[1],1,'Second snapshot')
        item=submit_request(db,db.get(User,citizen),RequestCreate(title='KTP elektronik',description='Saya perlu mengganti KTP elektronik yang hilang.'),classifier)
        from backend.app.models import ClassificationResult
        prediction=db.scalar(select(ClassificationResult).where(ClassificationResult.request_id==item.id))
        assert prediction.model_version==ids[0]
