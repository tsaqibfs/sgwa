import csv
import importlib.util
import json
from pathlib import Path
import pytest


def test_threshold_never_below_70_and_disables_when_no_candidate():
    assert importlib.util.find_spec('ml.evaluation'), 'Grouped evaluation not implemented'
    from ml.evaluation import choose_threshold
    policy=choose_threshold(['a']*30,['a']*30,[.70]*30)
    assert policy['threshold']==.70 and policy['auto_routing_enabled']
    assert policy['accepted_count']==30 and policy['coverage']==1
    assert not choose_threshold(['a']*30,['a']*30,[.699]*30)['auto_routing_enabled']
    assert not choose_threshold(['a']*30,['b']*30,[.95]*30)['auto_routing_enabled']
    assert not choose_threshold(['a']*24,['a']*24,[.95]*24)['auto_routing_enabled']


@pytest.fixture(scope='module')
def trained(tmp_path_factory):
    from ml.train import train
    folder=tmp_path_factory.mktemp('cv-artifact')
    report=train(Path('ml/data/requests.csv'),folder,holdout_path=Path('ml/data/holdout.json'))
    return folder,report


def test_cv_has_no_holdout_or_group_leakage(trained):
    folder,report=trained
    manifest=json.loads((folder/'manifest.json').read_text())
    holdout=set(json.loads(Path('ml/data/holdout.json').read_text())['groups'])
    assert report['train_count']==2000 and report['test_count']==500
    assert len(report['confusion_matrix'])==25
    assert len(report['cross_validation']['folds'])==5
    for fold in manifest['folds']:
        assert not set(fold['train_groups']) & set(fold['validation_groups'])
        assert not holdout & (set(fold['train_groups']) | set(fold['validation_groups']))
        assert len(fold['classes'])==25
    assert report['routing_policy']['threshold']>=.70
    assert report['provenance_counts']=={'synthetic':2500}


def test_each_fold_has_all_classes(tmp_path):
    assert importlib.util.find_spec('ml.evaluation'), 'Grouped evaluation not implemented'
    from ml.evaluation import evaluate_groups
    rows=[dict(text=f'class {label} group{i}',label=label,group_id=f'{label}-{i}') for label in ('a','b') for i in range(4)]
    with pytest.raises(ValueError,match='kelompok'):
        evaluate_groups(rows,{'groups':[]})


def test_artifact_identity_includes_training_config(trained,tmp_path):
    folder,_=trained
    from ml.train import validate_artifacts
    from shutil import copytree
    copied=tmp_path/'copy';copytree(folder,copied)
    info=json.loads((copied/'metadata.json').read_text())
    info['normalizer_version']='unknown'
    (copied/'metadata.json').write_text(json.dumps(info))
    with pytest.raises(ValueError):validate_artifacts(copied)
    info=json.loads((folder/'metadata.json').read_text())
    assert info['model_version'].startswith('ml25-')
    assert info['training_config']['C']==4


def test_repeated_training_matches_report(trained,tmp_path):
    from ml.train import train
    folder,report=trained
    other=train(Path('ml/data/requests.csv'),tmp_path,holdout_path=Path('ml/data/holdout.json'))
    assert other['macro_f1']==report['macro_f1']
    assert other['cross_validation']==report['cross_validation']
    assert other['model_version']==report['model_version']


def test_pipeline_excludes_validation_only_token():
    assert importlib.util.find_spec('ml.evaluation'), 'Grouped evaluation not implemented'
    from ml.evaluation import make_pipeline
    model=make_pipeline()
    model.fit(['vaksin puskesmas','puskesmas pasien','jalan aspal','jalan jembatan'],['a','a','b','b'])
    assert model.named_steps['tfidf'].transform(['zzvalidationonly']).nnz==0
