import pytest
from scripts.evaluate_ambiguity_pilot import keyword_decision, assess_decision, summarize


def test_keyword_baseline_does_not_choose_arbitrary_label_on_tie_or_no_match():
    words={'a':['akta'],'b':['sampah']}
    assert keyword_decision('akta dan sampah',words)['action']=='manual_review'
    assert keyword_decision('nomor itu belum jelas',words)['action']=='manual_review'
    assert keyword_decision('akta akta AKTA',words)['keyword_count']==1
    assert keyword_decision('fakta',words)['action']=='manual_review'
    assert keyword_decision('Akta kelahiran',words)['assigned_label']=='a'


def test_keyword_baseline_normalizes_alias_and_uses_distinct_phrases():
    result=keyword_decision('JLN rusak; ASPAL mengelupas.',{'road':['jalan','aspal']})
    assert result['assigned_label']=='road' and result['keyword_count']==2


def test_ambiguous_routing_and_clear_control_fallback_are_distinct():
    ambiguous={'preferred_action':'clarify','accepted_actions':['clarify','manual_review'],'expected_label':''}
    assert assess_decision('manual_review','',ambiguous)['appropriate_fallback']
    assert not assess_decision('manual_review','',ambiguous)['exact_preferred_action_match']
    forced=assess_decision('auto_route','a',ambiguous)
    assert forced['forced_route_on_review_case'] and forced['wrong_route_under_reference']
    clear={'preferred_action':'auto_route','accepted_actions':['auto_route'],'expected_label':'a'}
    assert assess_decision('manual_review','',clear)['fallback_on_clear_control']
    assert assess_decision('auto_route','b',clear)['wrong_route_under_reference']
    assert assess_decision('auto_route','a',clear)['decision_acceptable']


def test_summary_does_not_call_unmeasured_human_work_actual_corrections():
    ref={'preferred_action':'manual_review','accepted_actions':['manual_review'],'expected_label':''}
    row={'condition':'multi_issue','method':'final','action':'manual_review',**assess_decision('manual_review','',ref)}
    result=summarize([row])
    assert result['manual_review_count']==1 and result['appropriate_fallback_count']==1
    assert result['observed_human_corrections'] is None and result['observed_human_minutes'] is None
