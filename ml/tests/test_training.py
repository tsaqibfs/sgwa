import importlib.util
from pathlib import Path
import pytest


def test_training_has_group_isolation_and_dynamic_classes(tmp_path):
    assert importlib.util.find_spec('ml.train'), 'Training not implemented'
    from ml.train import train
    import csv
    rows = list(csv.DictReader(Path('ml/data/requests.csv').open(encoding='utf-8')))
    assert len(rows) >= 200
    assert all(sum(r['label'] == label for r in rows) >= 50 for label in {r['label'] for r in rows})
    report = train(Path('ml/data/requests.csv'), tmp_path)
    train_rows = list(csv.DictReader((tmp_path/'train.csv').open(encoding='utf-8')))
    test_rows = list(csv.DictReader((tmp_path/'test.csv').open(encoding='utf-8')))
    assert not {r['group_id'] for r in train_rows} & {r['group_id'] for r in test_rows}
    assert len(test_rows) == 500
    from backend.app.agencies.catalog import AGENCIES
    assert set(r['label'] for r in test_rows) == {code for code,_ in AGENCIES}
    assert 0 <= report['macro_f1'] <= 1
    assert len(report['confusion_matrix']) == 25
    other = tmp_path/'repeat'
    assert train(Path('ml/data/requests.csv'), other)['macro_f1'] == report['macro_f1']
    from backend.app.ml.classifier import Classifier
    classifier=Classifier(tmp_path)
    assert 'pendidikan' in classifier.predict('beasiswa sekolah pendidikan').probabilities


def test_inference_unknown_text_and_missing_artifact(tmp_path):
    assert importlib.util.find_spec('ml.train'), 'Training not implemented'
    from ml.train import train
    from backend.app.ml.classifier import Classifier, ModelUnavailable
    train(Path('ml/data/requests.csv'),tmp_path)
    clf=Classifier(tmp_path)
    prediction=clf.predict('Saya ingin mengurus KTP dan kartu keluarga di Dukcapil')
    assert prediction.agency_code == 'dukcapil'
    assert sum(prediction.probabilities.values()) == pytest.approx(1)
    assert prediction.known_features
    assert not clf.predict('zzzzz qqqqq xxxxx').known_features
    with pytest.raises(ModelUnavailable):
        Classifier(tmp_path/'missing')
