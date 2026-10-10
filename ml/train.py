"""Train trusted local artifacts; holdout never tunes routing policy."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import joblib
import sklearn
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from ml.build_dataset import canonical_hash, FIELDS
from ml.evaluation import CONFIG, evaluate_groups, make_pipeline
from ml.text import normalize_text, text_hash, NORMALIZER_VERSION


def validate_artifacts(directory: Path) -> dict:
    info=json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
    report=json.loads((directory/'evaluation.json').read_text(encoding='utf-8'))
    from backend.app.agencies.catalog import AGENCIES
    classes=sorted(code for code,_ in AGENCIES)
    if info['classes']!=classes or report['classes']!=classes or info['normalizer_version']!=NORMALIZER_VERSION:
        raise ValueError('Kelas atau normalizer artefak tidak valid')
    if report['model_version']!=info['model_version'] or report['holdout_manifest_hash']!=info['holdout_manifest_hash']:
        raise ValueError('Identitas laporan tidak cocok')
    policy=info['routing_policy']
    if not .70<=policy['threshold']<=.95 or not isinstance(policy['auto_routing_enabled'],bool) or len(report['cross_validation']['folds'])!=5:
        raise ValueError('Kebijakan routing atau CV tidak valid')
    if report['routing_policy']!=policy or info['threshold']!=policy['threshold']:
        raise ValueError('Kebijakan metadata dan laporan tidak cocok')
    def finite(value):
        if isinstance(value,float) and not math.isfinite(value):raise ValueError('Nilai numerik tidak finite')
        if isinstance(value,dict):
            for v in value.values():finite(v)
        if isinstance(value,list):
            for v in value:finite(v)
    finite(info);finite(report)
    for name,digest in info['artifact_hashes'].items():
        if name not in ('model.joblib','evaluation.json','manifest.json','train.csv','test.csv'):
            raise ValueError('Nama artefak tidak valid')
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Checksum artefak tidak cocok')
    if set(info['artifact_hashes'])!={'model.joblib','evaluation.json','manifest.json','train.csv','test.csv'}:
        raise ValueError('Artefak tidak lengkap')
    if info['model_hash']!=info['artifact_hashes']['model.joblib']:
        raise ValueError('Hash model tidak cocok')
    identity={k:info[k] for k in ('dataset_hash','training_config','normalizer_version','holdout_manifest_hash','feedback_snapshot_hash')}
    if info['model_version']!='ml25-'+canonical_hash(identity)[:24]:
        raise ValueError('Identitas model tidak valid')
    return info


def train(dataset_path: Path, output_dir: Path, *, holdout_path: Path | None=None, feedback_manifest: dict | None=None) -> dict:
    holdout_path=holdout_path or dataset_path.with_name('holdout.json')
    holdout=json.loads(holdout_path.read_text(encoding='utf-8'))
    if canonical_hash({k:v for k,v in holdout.items() if k!='manifest_hash'})!=holdout['manifest_hash']:
        raise ValueError('Manifest holdout diubah')
    with dataset_path.open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    from backend.app.agencies.catalog import AGENCIES
    labels=sorted({r['label'] for r in rows})
    if labels!=sorted(code for code,_ in AGENCIES):raise ValueError('Dataset harus memiliki tepat 25 label katalog')
    groups={};seen=set()
    for r in rows:
        if not r['text'].strip() or not r['group_id'].strip():raise ValueError('Teks dan group wajib')
        if r['group_id'] in groups and groups[r['group_id']]!=r['label']:raise ValueError('Kelompok memiliki konflik label')
        groups[r['group_id']]=r['label']
        digest=text_hash(r['text'])
        if digest in seen:raise ValueError('Teks duplikat setelah normalisasi')
        if r.get('text_hash')!=digest:raise ValueError('Hash teks tidak cocok')
        seen.add(digest)
        if r.get('provenance') not in ('synthetic','synthetic_demo','real'):raise ValueError('Provenance tidak valid')
    base=[r for r in rows if r['dataset_version']==holdout['dataset_version']]
    if canonical_hash(base)!=holdout['rows_hash']:raise ValueError('Dataset dasar tidak cocok dengan holdout tetap')
    if not set(holdout['groups'])<=set(groups):raise ValueError('Kelompok holdout hilang')
    cv=evaluate_groups(rows,holdout)
    train_rows=[r for r in rows if r['group_id'] not in holdout['groups']]
    test_rows=[r for r in rows if r['group_id'] in holdout['groups']]
    model=make_pipeline();model.fit([normalize_text(r['text']) for r in train_rows],[r['label'] for r in train_rows])
    predicted=model.predict([normalize_text(r['text']) for r in test_rows]);actual=[r['label'] for r in test_rows]
    dataset_hash=canonical_hash(rows)
    identity=dict(dataset_hash=dataset_hash,training_config=CONFIG,normalizer_version=NORMALIZER_VERSION,
                  holdout_manifest_hash=holdout['manifest_hash'],feedback_snapshot_hash=(feedback_manifest or {}).get('snapshot_hash',''))
    version='ml25-'+canonical_hash(identity)[:24]
    report=dict(model_version=version,macro_f1=float(f1_score(actual,predicted,average='macro',labels=labels,zero_division=0)),
                classification_report=classification_report(actual,predicted,labels=labels,output_dict=True,zero_division=0),
                confusion_matrix=confusion_matrix(actual,predicted,labels=labels).tolist(),classes=labels,
                train_count=len(train_rows),test_count=len(test_rows),train_groups=len(set(r['group_id'] for r in train_rows)),
                test_groups=len(set(r['group_id'] for r in test_rows)),random_state=42,synthetic=True,
                evaluation_provenance='synthetic_holdout',provenance_counts=dict(Counter(r['provenance'] for r in rows)),
                cross_validation={k:v for k,v in cv.items() if k!='routing_policy'},routing_policy=cv['routing_policy'],
                holdout_manifest_hash=holdout['manifest_hash'],normalizer_version=NORMALIZER_VERSION,
                errors=[dict(text=r['text'],actual=r['label'],predicted=str(p)) for r,p in zip(test_rows,predicted) if r['label']!=p])
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,subset in [('train.csv',train_rows),('test.csv',test_rows)]:
        with (output_dir/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(subset)
    joblib.dump(model,output_dir/'model.joblib')
    manifest=dict(holdout=holdout,folds=cv['folds'],feedback=feedback_manifest or {})
    for name,value in [('evaluation.json',report),('manifest.json',manifest)]:
        (output_dir/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    hashes={name:hashlib.sha256((output_dir/name).read_bytes()).hexdigest() for name in ('model.joblib','evaluation.json','manifest.json','train.csv','test.csv')}
    info={**identity,'model_version':version,'classes':labels,'artifact_hashes':hashes,'model_hash':hashes['model.joblib'],
          'synthetic':True,'evaluation_provenance':'synthetic_holdout','routing_policy':cv['routing_policy'],
          'threshold':cv['routing_policy']['threshold'],'sklearn_version':sklearn.__version__,'dataset_version':holdout['dataset_version']}
    (output_dir/'metadata.json').write_text(json.dumps(info,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    validate_artifacts(output_dir)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,default=Path('ml/data/requests.csv'));parser.add_argument('--output',type=Path,default=Path('ml/artifacts'));parser.add_argument('--holdout',type=Path,default=Path('ml/data/holdout.json'))
    args=parser.parse_args();report=train(args.dataset,args.output,holdout_path=args.holdout)
    print(f"Macro-F1: {report['macro_f1']:.4f}; test={report['test_count']}; holdout sintetis; threshold={report['routing_policy']['threshold']}")
