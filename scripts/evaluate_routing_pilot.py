"""Offline, read-only evaluation of a frozen routing pilot. Never trains a model.

Native example: python -m scripts.evaluate_routing_pilot --active-db --cases ...
Docker: copy this script and the two CSVs to /tmp, then run with PYTHONPATH=/app.
Use --allow-draft-labels only for explicitly provisional analysis.
"""
import argparse
import csv
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows, fields):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def align_reference(cases, references, labels, *, allow_draft=False):
    ids=[case['case_id'] for case in cases]
    ref_ids=[row['case_id'] for row in references]
    if len(ids)!=len(set(ids)) or len(ref_ids)!=len(set(ref_ids)) or set(ids)!=set(ref_ids):
        raise ValueError('ID teks dan label harus unik dan berpasangan lengkap.')
    index={row['case_id']:row for row in references}
    reviewed=all(row.get('review_status')=='approved' and all(row.get(field,'').strip() for field in
        ('reviewed_label','reviewer','reviewer_role','authority_evidence','reviewed_at')) for row in references)
    if not reviewed and not allow_draft:
        raise ValueError('Label belum selesai peninjauan; gunakan --allow-draft-labels hanya untuk analisis sementara.')
    key='reviewed_label' if reviewed else 'draft_label'
    actual=[index[case_id].get(key,'') for case_id in ids]
    if any(label not in labels for label in actual):raise ValueError('Label acuan di luar katalog model.')
    return actual,not reviewed


def routing_decision(*,auto_enabled,score,threshold,known_features,route):
    reasons=[]
    if not auto_enabled:reasons.append('auto_routing_disabled')
    if score<threshold:reasons.append('below_threshold')
    if not known_features:reasons.append('no_known_features')
    if not route:reasons.append('unavailable_route')
    return ('manual_review',reasons) if reasons else ('auto_route',[])


def score_predictions(predictions, actual, labels, *, provisional):
    if not predictions or len(predictions)!=len(actual):raise ValueError('Jumlah prediksi dan acuan tidak cocok.')
    predicted=[row['predicted_label'] for row in predictions]
    if any(value not in labels for value in predicted):raise ValueError('Prediksi di luar katalog.')
    accepted=[i for i,row in enumerate(predictions) if row['system_action']=='auto_route']
    class_report=classification_report(actual,predicted,labels=labels,output_dict=True,zero_division=0)
    correct=sum(a==p for a,p in zip(actual,predicted))
    automatic_correct=sum(bool(predictions[i]['route_codes']) and predictions[i]['route_codes'][0]==actual[i] for i in accepted)
    return dict(status='provisional_draft_labels' if provisional else 'reviewed_reference_evaluation',
        label_validity='AI draft labels; no verified human/domain ground truth' if provisional else 'See saved reference snapshot for reviewer role and authority evidence; approval is not proof of domain validation',
        sample_count=len(actual),classes=labels,support=dict(Counter(actual)),
        accuracy=float(accuracy_score(actual,predicted)),macro_f1=float(f1_score(actual,predicted,labels=labels,average='macro',zero_division=0)),
        recommendation_correct=correct,recommendation_wrong=len(actual)-correct,
        per_class={label:class_report[label] for label in labels},
        confusion_matrix=confusion_matrix(actual,predicted,labels=labels).tolist(),
        confusion_matrix_axes='rows=reference; columns=ML recommendation',
        manual_review_count=sum(row['system_action']=='manual_review' for row in predictions),
        auto_route_count=len(accepted),auto_route_coverage=len(accepted)/len(actual),
        automatic_wrong_primary_count=len(accepted)-automatic_correct,
        automatic_primary_accuracy=automatic_correct/len(accepted) if accepted else None,
        fallback_appropriateness=None,human_correction_workload=None,
        limits=['Balanced synthetic pilot, not resident population accuracy.',
                'Shared service themes and semantic overlap remain possible.',
                'Offline classifier and routing-policy evaluation; no HTTP authorization, admin actions, or staff completion tested.',
                'Manual review is a policy outcome, not evidence of an actual human correction.',
                'No ambiguity reference set or keyword baseline evaluated in this run.',
                'Model scores are not calibrated probabilities of correct authority.'])


def save_outputs(out,cases,references,predictions,actual,labels,provisional,snapshot):
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Folder hasil harus kosong agar run lama tidak tertimpa.')
    # Freeze input snapshots before releasing any predictions or scores.
    for name,rows in [('cases_frozen.csv',cases),('reference_frozen.csv',references)]:
        write_csv(out/name,rows,list(rows[0]))
    (out/'freeze.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps(predictions,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    flat=[];review=[]
    for case,pred,label in zip(cases,predictions,actual):
        flat.append(dict(case_id=case['case_id'],predicted_label=pred['predicted_label'],model_score=pred['model_score'],
            second_label=pred['second_label'],second_score=pred['second_score'],top_two_margin=pred['top_two_margin'],
            system_action=pred['system_action'],fallback_reasons=';'.join(pred['fallback_reasons']),
            automatic_primary=pred['route_codes'][0] if pred['system_action']=='auto_route' else '',
            model_version=snapshot['model_version'],actual_human_assignment='',actual_human_correction=''))
        review.append(dict(case_id=case['case_id'],priority='1_disagreement' if label!=pred['predicted_label'] else '2_small_margin' if pred['top_two_margin']<.05 else '3_other',
            title=case['title'],description=case['description'],reference_used=label,reference_status='AI_DRAFT' if provisional else 'REVIEWED',
            predicted_label=pred['predicted_label'],model_score=pred['model_score'],second_label=pred['second_label'],
            top_two_margin=pred['top_two_margin'],system_action=pred['system_action'],reviewer_comment='',failure_cause=''))
    write_csv(out/'predictions.csv',flat,list(flat[0]))
    review.sort(key=lambda row:(row['priority'],row['top_two_margin'],row['case_id']))
    write_csv(out/'review_priority.csv',review,list(review[0]))
    report=score_predictions(predictions,actual,labels,provisional=provisional)
    (out/'evaluation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    per_class=[dict(label=label,**report['per_class'][label]) for label in labels]
    write_csv(out/'per_class.csv',per_class,list(per_class[0]))
    matrix=[dict(reference_label=label,**dict(zip(labels,values))) for label,values in zip(labels,report['confusion_matrix'])]
    write_csv(out/'confusion_matrix.csv',matrix,['reference_label',*labels])
    hashes={p.name:digest(p) for p in out.iterdir() if p.is_file()}
    (out/'output_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('status','sample_count','recommendation_correct','recommendation_wrong','accuracy','macro_f1','manual_review_count','auto_route_count')},ensure_ascii=False))


def evaluate(args):
    from backend.app.agencies.catalog import AGENCIES
    from backend.app.ml.classifier import Classifier
    from ml.text import text_hash
    import sklearn
    cases=read_csv(args.cases);references=read_csv(args.reference)
    labels=sorted(code for code,_ in AGENCIES)
    if len(cases)!=500:raise ValueError('Pilot memerlukan tepat 500 teks.')
    actual,provisional=align_reference(cases,references,labels,allow_draft=args.allow_draft_labels)
    if Counter(actual)!=Counter({label:20 for label in labels}):raise ValueError('Pilot memerlukan tepat 20 acuan per kelas.')
    texts=[case['title']+' '+case['description'] for case in cases]
    if len({text_hash(text) for text in texts})!=500:raise ValueError('Ada teks berulang setelah normalisasi.')
    frozen_at=datetime.now(timezone.utc).isoformat()
    snapshot=dict(frozen_at=frozen_at,input_sha256=digest(args.cases),reference_sha256=digest(args.reference),
        code_revision=args.code_revision,python_version=platform.python_version(),sklearn_version=sklearn.__version__,
        label_mode='all_draft_labels' if provisional else 'all_reviewed_labels',inference_input='title + one space + description',
        driver='offline same Classifier.predict; no forms; same threshold/features/route checks; no request persistence',
        authority='No domain validation inferred from this automated run.',
        evaluator_sha256=digest(__file__),
        application_code_sha256={name:digest(name) for name in ('backend/app/ml/classifier.py','backend/app/requests/service.py','backend/app/workflow/routing.py')})
    if args.active_db:
        from sqlalchemy import select,text
        from sqlalchemy.orm import Session
        from backend.app.db import get_engine
        from backend.app.models import MLActiveModel,MLModelVersion,Agency,WorkflowRoute
        from backend.app.ml.registry import validated_version
        with Session(get_engine()) as db:
            db.execute(text('SET TRANSACTION READ ONLY'))
            pointer=db.get(MLActiveModel,1)
            if not pointer or not pointer.model_version_id:raise ValueError('Model aktif tidak tersedia.')
            row=db.get(MLModelVersion,pointer.model_version_id)
            directory,info,_=validated_version(row)
            model=Classifier(directory)
            agencies=db.scalars(select(Agency)).all()
            by_id={a.id:a for a in agencies};by_code={a.code:a for a in agencies}
            additional={label:[] for label in labels}
            for route in db.scalars(select(WorkflowRoute)):
                additional.setdefault(route.source_code,[]).append(route.agency_id)
            routes={}
            for label in labels:
                primary=by_code.get(label)
                ids=set(additional.get(label,[]))|({primary.id} if primary else set())
                routes[label]=[label]+[by_id[aid].code for aid in sorted(ids-{primary.id})] if primary and primary.active and all(aid in by_id and by_id[aid].active for aid in ids) else []
            snapshot.update(model_version=row.id,model_sha256=info['model_hash'],active_revision=pointer.revision,
                routing_policy=info['routing_policy'],routes=routes,active_agency_count=sum(a.active for a in agencies))
            # Session closes without commit; all database operations are SELECT.
    else:
        model=Classifier(Path(args.model_dir));info=model.info;directory=Path(args.model_dir)
        routes={label:[label] for label in labels}
        snapshot.update(model_version=info['model_version'],model_sha256=info['model_hash'],routing_policy=info['routing_policy'],
            routes=routes,route_source='ASSUMED identity mapping; no live database snapshot')
    if list(model.model.classes_)!=labels:raise ValueError('Model harus memiliki 25 kelas katalog yang sama.')
    overlaps={}
    for name in ('train.csv','test.csv'):
        existing={text_hash(row['text']) for row in read_csv(directory/name)}
        hits=[case['case_id'] for case in cases if text_hash(case['title']+' '+case['description']) in existing or text_hash(case['description']) in existing]
        overlaps[name]=len(hits)
        if hits:raise ValueError('Ada duplikasi persis dengan artefak training/holdout aktif.')
    snapshot['normalized_exact_overlap_against_active_artifacts']=overlaps
    predictions=[]
    for case,content in zip(cases,texts):
        prediction=model.predict(content)
        ranked=sorted(prediction.probabilities.items(),key=lambda item:item[1],reverse=True)
        route=routes.get(prediction.agency_code,[])
        action,reasons=routing_decision(auto_enabled=prediction.auto_routing_enabled,score=prediction.confidence,
            threshold=prediction.threshold,known_features=prediction.known_features,route=route)
        predictions.append(dict(case_id=case['case_id'],predicted_label=prediction.agency_code,model_score=prediction.confidence,
            second_label=ranked[1][0],second_score=ranked[1][1],top_two_margin=ranked[0][1]-ranked[1][1],
            system_action=action,fallback_reasons=reasons,route_codes=route,probabilities=prediction.probabilities))
    snapshot['completed_at']=datetime.now(timezone.utc).isoformat()
    if digest(args.cases)!=snapshot['input_sha256'] or digest(args.reference)!=snapshot['reference_sha256']:
        raise ValueError('Input berubah selama pengujian.')
    save_outputs(Path(args.output),cases,references,predictions,actual,labels,provisional,snapshot)


def rescore(args):
    """Reuse frozen predictions; never adjust the model after reading test results."""
    path=Path(args.rescore_predictions)
    original=json.loads((path.parent/'freeze.json').read_text(encoding='utf-8'))
    if digest(args.cases)!=original['input_sha256']:
        raise ValueError('Teks uji berubah; prediksi lama tidak dapat dipakai untuk teks baru.')
    predictions=json.loads(path.read_text(encoding='utf-8'))
    cases=read_csv(args.cases);references=read_csv(args.reference)
    labels=sorted(predictions[0]['probabilities'])
    actual,provisional=align_reference(cases,references,labels,allow_draft=args.allow_draft_labels)
    if [row['case_id'] for row in predictions]!=[row['case_id'] for row in cases]:
        raise ValueError('ID prediksi tidak cocok dengan urutan teks beku.')
    for row in references:
        case=next(case for case in cases if case['case_id']==row['case_id'])
        if any(key in row and row[key]!=case[key] for key in ('title','description')):
            raise ValueError('Teks di lembar review berubah dari teks yang diuji.')
    snapshot={**original,'rescored_at':datetime.now(timezone.utc).isoformat(),
        'reference_sha256':digest(args.reference),'original_reference_sha256':original['reference_sha256'],
        'predictions_sha256':digest(path),'scoring_code_revision':args.code_revision,'scoring_evaluator_sha256':digest(__file__),
        'label_review_timing':'Post-prediction review; do not claim reference labels were established blindly before this run.',
        'label_mode':'all_draft_labels' if provisional else 'all_reviewed_labels'}
    save_outputs(Path(args.output),cases,references,predictions,actual,labels,provisional,snapshot)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--active-db',action='store_true');source.add_argument('--model-dir');source.add_argument('--rescore-predictions')
    parser.add_argument('--cases',required=True);parser.add_argument('--reference',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--code-revision',required=True)
    parser.add_argument('--allow-draft-labels',action='store_true')
    args=parser.parse_args()
    rescore(args) if args.rescore_predictions else evaluate(args)


if __name__=='__main__':main()
