import csv
import importlib.util
import json
import pytest


def test_normalizer_is_conservative_and_idempotent():
    assert importlib.util.find_spec('ml.text'), 'Versioned normalizer not implemented'
    from ml.text import normalize_text
    assert normalize_text('JLN  bnyk lampmer') == 'jalan banyak lampu merah'
    assert normalize_text('TIDAK banjir di Paciran dan Bengawan Solo') == 'tidak banjir di paciran dan bengawan solo'
    assert normalize_text('jalan Paciran bukan jlnnya') == 'jalan paciran bukan jlnnya'
    assert normalize_text(normalize_text(' ＪＬＮ\t bnyk ')) == 'jalan banyak'
    with pytest.raises(ValueError):
        normalize_text('jalan', 'unknown')


def test_dataset_has_25_labels_and_stable_holdout(tmp_path):
    from ml import build_dataset as builder
    assert hasattr(builder, 'build_dataset'), '25-class generator not implemented'
    from backend.app.agencies.catalog import AGENCIES
    first=tmp_path/'first.csv'; manifest=tmp_path/'holdout.json'
    builder.build_dataset(first, manifest)
    rows=list(csv.DictReader(first.open(encoding='utf-8')))
    labels={r['label'] for r in rows}
    assert labels == {code for code,_ in AGENCIES}
    assert len(rows)==2500 and len({r['group_id'] for r in rows})==250
    assert all(sum(r['label']==label for r in rows)==100 for label in labels)
    assert len({r['text_hash'] for r in rows})==2500
    holdout=json.loads(manifest.read_text())
    assert len(holdout['groups'])==50
    assert all(len({r['group_id'] for r in rows if r['label']==label and r['group_id'] in holdout['groups']})==2 for label in labels)
    assert all(r['provenance']=='synthetic' for r in rows)
    second=tmp_path/'second.csv'; other=tmp_path/'other.json'
    builder.build_dataset(second,other)
    assert first.read_bytes()==second.read_bytes()
    assert manifest.read_bytes()==other.read_bytes()


def test_duplicate_normalized_text_is_rejected(tmp_path, monkeypatch):
    from ml import build_dataset as builder
    assert hasattr(builder, 'build_dataset'), '25-class generator not implemented'
    from ml.scenarios import SCENARIOS
    broken={code:list(values) for code,values in SCENARIOS.items()}
    broken['dukcapil'][1]=broken['dukcapil'][0]
    monkeypatch.setattr(builder,'SCENARIOS',broken)
    with pytest.raises(ValueError, match='duplikat'):
        builder.build_dataset(tmp_path/'bad.csv',tmp_path/'bad.json')
    assert not (tmp_path/'bad.csv').exists()
