"""Evidence-based manuscript review; preserves frozen results and visual assets."""
from pathlib import Path
import json
import re
import hashlib

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper-routing-15-pages/main.tex'
s=p.read_text(encoding='utf-8-sig')
original=s
(p.parent/'revision-history'/'before-scientific-review-20261030.tex').write_text(s,encoding='utf8')

def replace(old,new):
    global s
    assert s.count(old)==1,old[:100]
    s=s.replace(old,new,1)

replace('Evaluating Rule-Based Request Routing and Departmental Access Isolation in a Public Service Workflow',
        'Evaluating Request Recommendations and Departmental Access Isolation in a Public Service Workflow')
replace('Request routing and departmental access isolation','Request recommendations and departmental access isolation')
replace("This is a prototype scenario rather than an institutionally observed incident.",
        "No field observation, interview or agency-approved procedure establishes this scenario; it represents a prototype requirement.")
replace("Category identity mapping was active with no additional configured routing-rule rows.",
        "Category identity mapping was active with no additional configured routing-rule rows. Thus, the evaluated routing conditions are policy checks and category mappings, not a deployed keyword-rule classifier.")
anchor='A saved classification correction is a separate record and does not itself reroute a request.'
replace(anchor,anchor+' The access model permits citizens to read their own requests, administrators to review and assign requests, and staff to act on their assigned departmental tasks. On shared requests, task authority remains department-specific. Study~3 tests selected instances of these rules; Studies~1--2 do not exercise authorization.')
replace('An AI-authored, frozen corpus contains 500 new texts and proposed reference categories, 20 per category.',
        'An AI-authored corpus contains 500 texts and proposed single-label references, 20 per category. Texts, labels and label reasons were frozen before inference; the proposed labels were not independently adjudicated.')
replace('The same AI author conducted a later non-blind review; no independent human/domain validation occurred.',
        'The same AI author later reviewed all 500 cases, including all 51 disagreements, with predictions visible; no independent human/domain validation occurred.')
replace('Both methods used the same frozen cases.',
        'Cases, proposed actions and comparator phrases were frozen before model inference; both methods used the same cases. Exact normalized overlap with the deployed training and holdout files was checked, but semantic independence is not established.')
replace('This tests one fixed comparator, not rule-based methods generally.',
        'Manual-review counts measure queue referrals; correction counts, review duration and final human assignments were not observed. This tests one fixed comparator, not rule-based methods generally.')
replace('We compare expected/actual HTTP status and pre/post hashes of nine protected business tables and files.',
        'We compare expected/actual HTTP status and pre/post hashes of nine protected business tables and file fixtures, including request history and audit records. Terminal fixtures cover forbidden reopening; positive controls also create terminal states through API actions.')
replace('These are recommendation results, not 449 completed departmental assignments.',
        'The remaining 51 inputs disagreed with the proposed labels. These are recommendation results; final administrator assignments and completed services were not measured.')
replace('Mandatory review explains the conservative outcome, not demonstrated ambiguity detection or classifier superiority.',
        'Mandatory review explains the conservative outcome. The 19/25 versus 20/25 acceptable-action counts are descriptive policy outcomes under AI-authored references, not evidence of classifier superiority or a semantic ambiguity detector.')
replace('These are selected in-process tests, not a complete security audit.',
        'ML inference was disabled in this pilot, so these access results cannot establish secure end-to-end routing across all 25 categories. They support only the selected in-process cases, not a complete security audit.')
replace('Without the complete input, model version, score or final assignment, this report was not reproduced and does not establish data disclosure.',
        'The complete input, model version, score and final assignment were unavailable; the category error remains participant-reported, with no established disclosure. The password report is an interface issue, not evidence of a routing failure.')
replace('Independent domain labels, observed staff review decisions and a documented participant protocol remain necessary; wording changes cannot substitute for these missing data. Further domain review, independent cases and observed staff corrections are necessary.',
        'Independent domain labels, observed staff decisions and a documented participant protocol remain necessary. Consequently, these studies answer different parts of the research question; they do not establish jointly correct and secure service completion in operational use.')
replace('The 25-class synthetic pilot produced 449/500 provisional recommendation matches and macro-F1 0.8969. Mandatory review prevented forced routing in the 20 ambiguity cases but also deferred all five clear controls; it demonstrates a cautious policy and potential review burden, not an ambiguity detector. All 61 selected API cases met expected outcomes and all 37 rejected actions preserved the checked business tables. Five participant sessions were recorded as independent, with three password-visibility comments and one reported KK (Family Card) category error. Thus the question is only partially answered: domain-valid jurisdiction accuracy, actual human correction workload and broader access coverage remain open. Real-world validation and documented usability protocols are required before claiming improved service outcomes.',
        'The research question is partially answered within the prototype: 449/500 recommendations matched provisional AI-authored labels (macro-F1 0.8969); mandatory review avoided forced assignments on 20 ambiguous inputs but also deferred all five clear controls. All 61 selected API cases met expected outcomes, and 37 rejected actions preserved the nine checked business tables and file fixtures. These separate tests support provisional recommendation agreement, conservative review behavior and selected access/state safeguards. Five testers supplied exploratory interface feedback, including three password-visibility comments and one unverified family-card category error. Domain-valid destinations, final human assignments, correction workload and integrated routing/access performance remain unestablished. Independent domain review and documented user studies are required before claiming improved service outcomes or reduced service time.')
start=s.index('\\begin{abstract}')
end=s.index('\\keywords{',start)
s=s[:start]+r'''\begin{abstract}
Public service workflows must identify suitable departmental destinations while restricting access to authorized users. This study evaluates Smart Government Workflow Automation (SGWA), a web prototype with 25-category text recommendations, department mapping, mandatory administrator review and request-specific authorization. Three complementary pilots assessed recommendation agreement, ambiguity handling against a fixed keyword comparator, and access/state guards. Among 500 AI-authored texts with proposed labels frozen before inference, 449 recommendations agreed (89.8\%; macro-F1 0.8969). On 20 ambiguous scenarios and five clear controls, the comparator forced six ambiguous assignments; the active policy deferred all 25 inputs because automatic routing was disabled. In an isolated MySQL/API pilot, 61 selected cases met expected outcomes and 37 rejected actions preserved nine protected tables and file fixtures. Five testers supplied exploratory interface feedback; incomplete task and timing records preclude efficiency claims. These results support provisional agreement and selected safeguards, but not independently validated jurisdiction accuracy, effective human correction or secure end-to-end service completion. Domain validation and documented user studies remain necessary.
'''+s[end:]

# Verify the entire plotted matrix and every supplied result row stay intact.
oldcells=re.findall(r'\((\d+),(\d+)\) \[(\d+)\]',original)
assert len(oldcells)==625
assert oldcells==re.findall(r'\((\d+),(\d+)\) \[(\d+)\]',s)
for name in ['tab:perclass','tab:ambiguity','tab:access','tab:endpoint-cases','tab:usability']:
    pattern=r'\\begin\{table\}.*?\\end\{table\}'
    a=next(m.group() for m in re.finditer(pattern,original,re.S) if r'\label{'+name+'}' in m.group())
    b=next(m.group() for m in re.finditer(pattern,s,re.S) if r'\label{'+name+'}' in m.group())
    assert a==b,name

e1=json.loads((ROOT/'outputs/routing-evaluation-20261025-provisional/evaluation.json').read_text())
e2=json.loads((ROOT/'outputs/ambiguity-evaluation-20261025-provisional/evaluation.json').read_text())
cases=json.loads((ROOT/'outputs/access-terminal-pilot-20261025/run-04/cases.json').read_text())
matrix=[[int(n) for x,y,n in oldcells if int(y)==row] for row in range(1,26)]
assert matrix==e1['confusion_matrix']
assert sum(sum(r) for r in matrix)==500 and sum(matrix[i][i] for i in range(25))==449
assert all(sum(r)==20 for r in matrix)
macro=sum(v['f1-score'] for v in e1['per_class'].values())/25
assert abs(macro-e1['macro_f1'])<1e-12
assert len(cases)==61 and all(c['passed'] for c in cases)
denied=[c for c in cases if c['actual_status']>=400]
assert len(denied)==37 and all(c['checks']['protected_database_and_files_unchanged'] for c in denied)
assert [e2['methods'][k]['all_25']['decision_acceptable_count'] for k in ['keyword_baseline','final_ml_policy']]==[19,20]
order=[]
for g in re.findall(r'\\cite\{([^}]+)\}',s):
    for key in g.split(','):
        if key not in order: order.append(key)
assert order==re.findall(r'\\bibitem\{([^}]+)\}',s)
labels=re.findall(r'\\label\{([^}]+)\}',s)
assert len(labels)==len(set(labels))
assert set(re.findall(r'\\ref\{([^}]+)\}',s))<=set(labels)
images=re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',s)
assert all((p.parent/im).is_file() for im in images)
p.write_text(s,encoding='utf8',newline='\n')
out=p.parent/'review-20261030'
out.mkdir(exist_ok=True)
(out/'audit.json').write_text(json.dumps(dict(status='checked_against_frozen_evidence',study1=dict(n=500,agreement=449,disagreement=51,macro_f1=macro,matrix_cells=625),study2=dict(acceptable_actions=[19,20],review_counts=[14,25],human_review_time_observed=False),study3=dict(cases=61,passed=61,denied=37,denied_storage_unchanged=37),bibliography_entries=len(order),all_numeric_tables_preserved=True,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2),encoding='utf8')
print('Reviewed manuscript; all 625 cells, numeric tables, citation order and source images verified.')
