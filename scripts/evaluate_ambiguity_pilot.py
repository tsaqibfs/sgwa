"""Uji 2: frozen keyword comparator versus active ML routing policy, read-only."""
import argparse
import json
import re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from ml.text import normalize_text,text_hash
from scripts.evaluate_routing_pilot import digest,write_csv,routing_decision


def keyword_decision(content,keywords):
    content=normalize_text(content)
    matched={label:[word for word in dict.fromkeys(normalize_text(word) for word in words)
                    if re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',content)] for label,words in keywords.items()}
    scores={label:len(words) for label,words in matched.items()}
    top=max(scores.values(),default=0)
    winners=sorted(label for label,count in scores.items() if top and count==top)
    chosen=winners[0] if len(winners)==1 else ''
    return dict(action='auto_route' if chosen else 'manual_review',assigned_label=chosen,
        keyword_count=top,matched_keywords=matched,tied_labels=winners if len(winners)>1 else [])


def assess_decision(action,assigned_label,reference):
    if action not in ('auto_route','manual_review','clarify','external_referral'):
        raise ValueError('Unknown decision action')
    clear=reference['preferred_action']=='auto_route'
    routing=action=='auto_route'
    forced=routing and not clear
    wrong_control=routing and clear and assigned_label!=reference['expected_label']
    fallback=action in ('manual_review','clarify')
    acceptable=action in reference['accepted_actions'] and (not routing or assigned_label==reference['expected_label'])
    return dict(decision_acceptable=acceptable,
        exact_preferred_action_match=action==reference['preferred_action'] and (not routing or assigned_label==reference['expected_label']),
        appropriate_fallback=fallback and not clear and action in reference['accepted_actions'],
        forced_route_on_review_case=forced,wrong_control_route=wrong_control,
        wrong_route_under_reference=forced or wrong_control,fallback_on_clear_control=fallback and clear)


def summarize(rows):
    return dict(case_count=len(rows),decision_acceptable_count=sum(r['decision_acceptable'] for r in rows),
        exact_preferred_action_match_count=sum(r['exact_preferred_action_match'] for r in rows),
        auto_route_count=sum(r['action']=='auto_route' for r in rows),
        manual_review_count=sum(r['action']=='manual_review' for r in rows),
        clarification_count=sum(r['action']=='clarify' for r in rows),
        appropriate_fallback_count=sum(r['appropriate_fallback'] for r in rows),
        forced_route_on_review_case_count=sum(r['forced_route_on_review_case'] for r in rows),
        wrong_control_route_count=sum(r['wrong_control_route'] for r in rows),
        wrong_route_under_reference_count=sum(r['wrong_route_under_reference'] for r in rows),
        fallback_on_clear_control_count=sum(r['fallback_on_clear_control'] for r in rows),
        observed_human_corrections=None,observed_human_minutes=None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('dataset','baseline','output','expected-model-id','code-revision'):parser.add_argument('--'+arg,required=True)
    args=parser.parse_args()
    from sqlalchemy import select,text
    from sqlalchemy.orm import Session
    from backend.app.db import get_engine
    from backend.app.models import MLActiveModel,MLModelVersion,Agency,WorkflowRoute
    from backend.app.agencies.catalog import AGENCIES
    from backend.app.ml.registry import validated_version
    from backend.app.ml.classifier import Classifier
    import sklearn
    dataset=json.loads(Path(args.dataset).read_text(encoding='utf-8'))
    baseline=json.loads(Path(args.baseline).read_text(encoding='utf-8'))
    cases=dataset['cases'];labels=sorted(code for code,_ in AGENCIES)
    expected_counts={condition:5 for condition in ('minimal_information','multi_issue','out_of_scope','missing_scope_context','clear_control')}
    if Counter(row['condition'] for row in cases)!=Counter(expected_counts):raise ValueError('Require 20 ambiguity cases plus 5 controls.')
    if set(baseline['keywords'])!=set(labels):raise ValueError('Baseline must cover all 25 prototype categories.')
    if len({r['case_id'] for r in cases})!=25:raise ValueError('Duplicate case IDs')
    texts=[row['title']+' '+row['description'] for row in cases]
    if len({text_hash(t) for t in texts})!=25:raise ValueError('Duplicate normalized input')
    for row in cases:
        if len(row['title'])<5 or len(row['description'])<20:raise ValueError('Text does not meet web form minimum lengths')
        if row['condition']=='clear_control' and row['expected_label'] not in labels:raise ValueError('Invalid control label')
        if row['condition']!='clear_control' and row['expected_label']:raise ValueError('Do not force single labels on ambiguity cases')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new empty output directory')
    frozen_at=datetime.now(timezone.utc).isoformat()
    dataset_hash=digest(args.dataset);baseline_hash=digest(args.baseline)
    # Persist the exact reference and baseline BEFORE the first model prediction.
    (out/'cases_reference_frozen.json').write_bytes(Path(args.dataset).read_bytes())
    (out/'baseline_frozen.json').write_bytes(Path(args.baseline).read_bytes())
    with Session(get_engine()) as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        pointer=db.get(MLActiveModel,1)
        if not pointer or pointer.model_version_id!=args.expected_model_id:raise ValueError('Active model differs from declared experiment model')
        model_row=db.get(MLModelVersion,pointer.model_version_id)
        directory,info,_=validated_version(model_row);model=Classifier(directory)
        if list(model.model.classes_)!=labels:raise ValueError('Model category mismatch')
        agencies=db.scalars(select(Agency)).all();by_id={a.id:a for a in agencies};by_code={a.code:a for a in agencies}
        extras={label:set() for label in labels}
        for row in db.scalars(select(WorkflowRoute)):extras.setdefault(row.source_code,set()).add(row.agency_id)
        routes={}
        for label in labels:
            primary=by_code.get(label);ids=extras[label]|({primary.id} if primary else set())
            routes[label]=[label]+[by_id[i].code for i in sorted(ids-{primary.id})] if primary and primary.active and all(i in by_id and by_id[i].active for i in ids) else []
        snapshot=dict(frozen_at=frozen_at,dataset_sha256=dataset_hash,baseline_sha256=baseline_hash,
            reference_status=dataset['reference_status'],code_revision=args.code_revision,evaluator_sha256=digest(__file__),
            shared_evaluator_sha256=digest(Path(__file__).with_name('evaluate_routing_pilot.py')),
            application_code_sha256={name:digest(name) for name in ('backend/app/ml/classifier.py','backend/app/requests/service.py','backend/app/workflow/routing.py')},
            model_version=model_row.id,model_sha256=info['model_hash'],active_revision=pointer.revision,
            sklearn_version=sklearn.__version__,routing_policy=info['routing_policy'],routes=routes,
            execution='Offline same Classifier.predict; no HTTP endpoint or saved requests; read-only MySQL transaction',
            normalization='id-v1',baseline_id=baseline['baseline_id'])
    (out/'freeze.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Check exact overlap against the actual deployed model artefacts.
    from scripts.evaluate_routing_pilot import read_csv
    existing={text_hash(row['text']) for name in ('train.csv','test.csv') for row in read_csv(directory/name)}
    if any(text_hash(t) in existing for t in texts):raise ValueError('Exact normalized overlap with deployed training/holdout')
    all_results=[];paired=[];raw=[]
    for case,content in zip(cases,texts):
        simple=keyword_decision(content,baseline['keywords'])
        prediction=model.predict(content);route=routes[prediction.agency_code]
        action,reasons=routing_decision(auto_enabled=prediction.auto_routing_enabled,score=prediction.confidence,
            threshold=prediction.threshold,known_features=prediction.known_features,route=route)
        assigned=route[0] if action=='auto_route' else ''
        left=assess_decision(simple['action'],simple['assigned_label'],case)
        right=assess_decision(action,assigned,case)
        for method,decision,verdict in [('keyword_baseline',simple['action'],left),('final_ml_policy',action,right)]:
            all_results.append(dict(case_id=case['case_id'],condition=case['condition'],method=method,action=decision,**verdict))
        paired.append(dict(case_id=case['case_id'],condition=case['condition'],title=case['title'],description=case['description'],
            preferred_action=case['preferred_action'],accepted_actions=';'.join(case['accepted_actions']),expected_label=case['expected_label'],reference_reason=case['reason'],
            baseline_action=simple['action'],baseline_assigned_label=simple['assigned_label'],baseline_keyword_count=simple['keyword_count'],
            baseline_wrong_route=left['wrong_route_under_reference'],baseline_appropriate_fallback=left['appropriate_fallback'],baseline_fallback_on_clear=left['fallback_on_clear_control'],
            final_action=action,final_recommended_label=prediction.agency_code,final_model_score=prediction.confidence,final_assigned_label=assigned,
            final_wrong_route=right['wrong_route_under_reference'],final_appropriate_fallback=right['appropriate_fallback'],final_fallback_on_clear=right['fallback_on_clear_control'],
            final_fallback_reasons=';'.join(reasons),human_review_note=''))
        raw.append(dict(case_id=case['case_id'],baseline=simple,final=dict(action=action,assigned_label=assigned,
            recommendation=prediction.agency_code,probabilities=prediction.probabilities,model_score=prediction.confidence,fallback_reasons=reasons),
            baseline_assessment=left,final_assessment=right))
    if digest(args.dataset)!=dataset_hash or digest(args.baseline)!=baseline_hash:raise ValueError('Experiment inputs changed during execution')
    summaries={};by_condition=[]
    for method in ('keyword_baseline','final_ml_policy'):
        rows=[r for r in all_results if r['method']==method]
        summaries[method]=dict(all_25=summarize(rows),ambiguity_20=summarize([r for r in rows if r['condition']!='clear_control']),clear_controls_5=summarize([r for r in rows if r['condition']=='clear_control']))
        for condition in expected_counts:by_condition.append(dict(method=method,condition=condition,**summarize([r for r in rows if r['condition']==condition])))
    report=dict(status='provisional_AI_synthetic_reference',methods=summaries,
        reference_provenance=dataset['provenance'],baseline_provenance=baseline['provenance'],
        limits=['Both references and comparator authored by AI; no independent domain validation.',
            '20 ambiguity cases plus 5 separate clear controls; no multiclass confusion matrix forced onto these cases.',
            'manual_review allowed as coarse fallback where clarify is preferred; actual automated clarification not implemented.',
            'Wrong route means a forced route on a review-required case or wrong primary category on a control, under provisional reference.',
            'Fallback on clear controls is workload under a semantic reference, not proof that ignoring confidence policy would be safe.',
            'If final always reviews, appropriate fallback is not evidence of a semantic ambiguity detector.',
            'Manual-review counts are routing decisions, not measured human corrections, time, or usability.',
            'A fixed keyword comparator is one limited baseline; results do not establish superiority over rule-based systems in general.'])
    write_csv(out/'decision_comparison.csv',paired,list(paired[0]));write_csv(out/'condition_results.csv',by_condition,list(by_condition[0]));write_csv(out/'decision_log.csv',all_results,list(all_results[0]))
    for name,data in [('raw_predictions.json',raw),('evaluation.json',report)]:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'output_hashes.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir() if p.is_file()},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({method:data['all_25'] for method,data in summaries.items()},ensure_ascii=False))


if __name__=='__main__':main()
