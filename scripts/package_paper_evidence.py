"""Copy selected frozen evidence and validate manuscript figures/tables."""
import csv
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'paper-routing-study'
files = {
    'study-1/cases.csv': 'research/routing-pilot-v1/teks_uji_500.csv',
    'study-1/provisional-reference.csv': 'research/routing-pilot-v1/label_acuan_500.csv',
    'study-1/evaluation.json': 'outputs/routing-evaluation-20261025-provisional/evaluation.json',
    'study-1/per-class.csv': 'outputs/routing-evaluation-20261025-provisional/per_class.csv',
    'study-1/confusion-matrix.csv': 'outputs/routing-evaluation-20261025-provisional/confusion_matrix.csv',
    'study-1/freeze.json': 'outputs/routing-evaluation-20261025-provisional/freeze.json',
    'study-1/ai-review-summary.json': 'outputs/routing-ai-review-20261025/ai_review_summary.json',
    'study-2/cases-and-reference.json': 'outputs/ambiguity-evaluation-20261025-provisional/cases_reference_frozen.json',
    'study-2/baseline.json': 'outputs/ambiguity-evaluation-20261025-provisional/baseline_frozen.json',
    'study-2/evaluation.json': 'outputs/ambiguity-evaluation-20261025-provisional/evaluation.json',
    'study-2/comparison.csv': 'outputs/ambiguity-evaluation-20261025-provisional/decision_comparison.csv',
    'study-2/conditions.csv': 'outputs/ambiguity-evaluation-20261025-provisional/condition_results.csv',
    'study-2/freeze.json': 'outputs/ambiguity-evaluation-20261025-provisional/freeze.json',
    'study-3/summary.json': 'outputs/access-terminal-pilot-20261025/summary.json',
    'study-3/case-matrix.csv': 'outputs/access-terminal-pilot-20261025/case_matrix.csv',
    'study-3/database-checks.csv': 'outputs/access-terminal-pilot-20261025/database_checks.csv',
    'study-3/run-metadata.json': 'outputs/access-terminal-pilot-20261025/run-04/run_metadata.json',
    'study-3/test-log.txt': 'outputs/access-terminal-pilot-20261025/run-04/pytest.log',
}
manifest = []
for dest, src in files.items():
    source = ROOT / src
    target = PROJECT / 'evidence' / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    manifest.append({'file': 'evidence/' + dest, 'source': src,
                     'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
(PROJECT / 'source-map.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

tex = (PROJECT / 'main.tex').read_text(encoding='utf-8-sig')
labels = re.findall(r'\\label\{([^}]+)\}', tex)
assert len(labels) == len(set(labels)), 'Duplicate LaTeX labels'
assert set(re.findall(r'\\ref\{([^}]+)\}', tex)) <= set(labels), 'Unresolved reference'
citations = {key.strip() for group in re.findall(r'\\cite\{([^}]+)\}', tex) for key in group.split(',')}
assert citations <= set(re.findall(r'\\bibitem\{([^}]+)\}', tex)), 'Missing bibliography key'
assert not re.search(r'__(RELATED|PERCLASS|F1COORDS|CMCOORDS|BIB)__', tex)
assert tex.strip().endswith(r'\end{document}')
assert not any(ord(c)<32 and c not in '\n\t\r' for c in tex), 'Invalid source control character'
images = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', tex)
assert len(images) == 5, 'Expected five supplied prototype screenshots'
assert all((PROJECT / image).is_file() for image in images), 'Missing image file'
perclass = list(csv.DictReader((PROJECT / 'evidence/study-1/per-class.csv').open(encoding='utf-8-sig')))
matrix = list(csv.reader((PROJECT / 'evidence/study-1/confusion-matrix.csv').open(encoding='utf-8-sig')))
numeric = [[int(n) for n in row[1:]] for row in matrix[1:]]
assert len(perclass) == len(numeric) == 25
assert all(sum(row) == 20 for row in numeric)
assert sum(numeric[i][i] for i in range(25)) == 449
macro = sum(float(r['f1-score']) for r in perclass)/25
assert abs(macro - .8969491545305445) < 1e-12
for i,r in enumerate(perclass):
    expected = f"{100*float(r['precision']):.1f} & {100*float(r['recall']):.1f} & {100*float(r['f1-score']):.1f}"
    assert expected in tex, f'Incorrect row {i+1}'
access = json.loads((PROJECT/'evidence/study-3/summary.json').read_text())
assert access['case_count'] == access['passed'] == 61
assert access['denied_cases'] == access['denied_business_unchanged'] == 37
assert access['denied_database_table_checks'] == 333
assert access['database_checks'] == 549
ambiguity = json.loads((PROJECT/'evidence/study-2/evaluation.json').read_text())['methods']
assert ambiguity['keyword_baseline']['ambiguity_20']['forced_route_on_review_case_count'] == 6
assert ambiguity['final_ml_policy']['all_25']['manual_review_count'] == 25
verification = {'study_1': {'n':500,'matching':449,'disagreements':51,'macro_f1':macro},
                'study_2': {'ambiguous':20,'controls':5,'baseline_forced':6,'final_manual':25},
                'study_3': {'cases':61,'met_expected':61,'denied':37,'table_checks':549},
                'latex_labels':len(labels),'citation_keys':len(citations),
                'evidence_files':len(manifest),'prototype_screenshots':len(images),'static_checks':'passed',
                'bibliography_entries':len(re.findall(r'\\bibitem\{',tex)),
                'doi_entries':len(re.findall(r'\\doi\{',tex)),
                'note':'Static consistency checks do not replace LaTeX compilation or human/domain review.'}
(PROJECT/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/'paper-routing-study-overleaf.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(PROJECT.rglob('*')):
        if file.is_file() and file.suffix not in {'.aux','.log','.out','.toc'}:
            archive.write(file, file.relative_to(PROJECT).as_posix())
print(json.dumps(verification,indent=2))
