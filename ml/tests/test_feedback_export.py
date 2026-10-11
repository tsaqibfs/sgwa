import csv
import importlib.util
import json
from pathlib import Path
import pytest

def sample(i,text,label='dukcapil',family=None,request=None):
    return dict(id=i,request_id=request or i,revision=1,training_text=text,corrected_code=label,provenance='synthetic_demo',family_key=family)

def merge(entries):
    assert importlib.util.find_spec('backend.app.ml.feedback_export'), 'Feedback exporter missing'
    from backend.app.ml.feedback_export import merge_feedback
    from ml.build_dataset import canonical_hash
    with Path('ml/data/requests.csv').open(encoding='utf-8') as f:base=list(csv.DictReader(f))
    holdout=json.loads(Path('ml/data/holdout.json').read_text())
    return merge_feedback(base,holdout,{'entries':entries,'snapshot_hash':canonical_hash(entries)})

def test_duplicate_conflicting_normalized_feedback_is_rejected():
    with pytest.raises(ValueError,match='label'):
        merge([sample(1,'JLN bnyk rusak','pu_bina_marga'),sample(2,'jalan banyak rusak','perhubungan')])

def test_family_and_request_groups_are_transitively_isolated():
    rows,manifest=merge([sample(1,'Kartu identitas perlu dicetak ulang',family='family-a',request=8),
                         sample(2,'Rekam data penduduk baru',family='family-a',request=9),
                         sample(3,'Kartu identitas perlu dicetak ulang',request=10),
                         sample(4,'Memperbarui domisili keluarga penduduk',request=10)])
    extra=[r for r in rows if r['dataset_version']=='feedback-v1']
    assert len(extra)==3 and len({r['group_id'] for r in extra})==1
    assert len(manifest['included'])==3 and len(manifest['excluded'])==1

def test_holdout_overlap_excludes_entire_family():
    assert importlib.util.find_spec('backend.app.ml.feedback_export'), 'Feedback exporter missing'
    with Path('ml/data/requests.csv').open(encoding='utf-8') as f:base=list(csv.DictReader(f))
    holdout=json.loads(Path('ml/data/holdout.json').read_text())
    item=next(r for r in base if r['group_id'] in holdout['groups'])
    rows,manifest=merge([sample(1,item['text'],item['label'],family='same-family'),
                         sample(2,'Kalimat baru untuk skenario holdout',item['label'],family='same-family')])
    assert len(rows)==2500 and len(manifest['excluded'])==2
    assert all(r['reason']=='holdout_overlap' for r in manifest['excluded'])

def test_base_training_overlap_uses_base_group_and_mixed_provenance():
    assert importlib.util.find_spec('backend.app.ml.feedback_export'), 'Feedback exporter missing'
    with Path('ml/data/requests.csv').open(encoding='utf-8') as f:base=list(csv.DictReader(f))
    holdout=json.loads(Path('ml/data/holdout.json').read_text())
    item=next(r for r in base if r['group_id'] not in holdout['groups'])
    entries=[sample(1,item['text'],item['label'],family='existing'),sample(2,'Teks baru yang disunting manual oleh petugas',item['label'],family='existing')]
    entries[1]['provenance']='real'
    rows,manifest=merge(entries)
    assert len(rows)==2501 and rows[-1]['group_id']==item['group_id'] and rows[-1]['provenance']=='real'

def test_family_conflicting_labels_and_multiple_base_groups_rejected():
    with pytest.raises(ValueError,match='label'):
        merge([sample(1,'Layanan KTP',family='one'),sample(2,'Beasiswa siswa','pendidikan',family='one')])
