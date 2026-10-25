import pytest

from scripts.evaluate_routing_pilot import align_reference, routing_decision, score_predictions


def test_alignment_uses_ids_and_rejects_missing_or_unreviewed_reference():
    cases=[{'case_id':'A'},{'case_id':'B'}]
    refs=[{'case_id':'B','draft_label':'two','reviewed_label':'','review_status':'pending'},
          {'case_id':'A','draft_label':'one','reviewed_label':'','review_status':'pending'}]
    assert align_reference(cases,refs,['one','two'],allow_draft=True)==(['one','two'],True)
    with pytest.raises(ValueError,match='peninjauan'):
        align_reference(cases,refs,['one','two'],allow_draft=False)
    with pytest.raises(ValueError,match='ID'):
        align_reference(cases,refs[:1],['one','two'],allow_draft=True)


def test_reviewed_reference_requires_real_review_metadata_and_no_mixed_labels():
    ref={'case_id':'A','draft_label':'one','reviewed_label':'two','review_status':'approved',
         'reviewer':'Reviewer','reviewer_role':'mahasiswa','authority_evidence':'Asumsi skenario','reviewed_at':'2026-10-25T07:00:00+07:00'}
    assert align_reference([{'case_id':'A'}],[ref],['one','two'],allow_draft=False)==(['two'],False)
    ref['reviewer']=''
    with pytest.raises(ValueError,match='peninjauan'):
        align_reference([{'case_id':'A'}],[ref],['one','two'],allow_draft=False)


def test_disabled_auto_routing_is_fallback_even_for_correct_high_score():
    assert routing_decision(auto_enabled=False,score=.99,threshold=.7,known_features=True,route=['one'])==('manual_review',['auto_routing_disabled'])
    assert routing_decision(auto_enabled=True,score=.99,threshold=.7,known_features=True,route=['one'])==('auto_route',[])
    action,reasons=routing_decision(auto_enabled=True,score=.2,threshold=.7,known_features=False,route=[])
    assert action=='manual_review' and set(reasons)=={'below_threshold','no_known_features','unavailable_route'}


def test_scores_keep_recommendation_errors_separate_from_manual_fallback():
    predictions=[{'case_id':'A','predicted_label':'one','system_action':'manual_review','route_codes':[]},
                 {'case_id':'B','predicted_label':'one','system_action':'manual_review','route_codes':[]}]
    report=score_predictions(predictions,['one','two'],['one','two'],provisional=True)
    assert report['recommendation_correct']==1 and report['recommendation_wrong']==1
    assert report['confusion_matrix']==[[1,0],[1,0]]
    assert report['manual_review_count']==2 and report['auto_route_count']==0
    assert report['automatic_wrong_primary_count']==0
    assert report['automatic_primary_accuracy'] is None
    assert report['macro_f1']==pytest.approx(1/3)
    assert report['per_class']['two']['support']==1 and report['status']=='provisional_draft_labels'
