"""Package existing, explicitly selected research evidence; no database mutation."""
from pathlib import Path
import hashlib
import json
import zipfile

root=Path(__file__).resolve().parents[1]
paper=root/'paper-routing-15-pages'
archive=root/'paper-routing-reviewed-evidence-20261030.zip'
paths={}
def add(path, dest=None):
    path=Path(path)
    assert path.is_file(),path
    paths[dest or path.relative_to(root).as_posix()]=path

add(paper/'main.tex','paper/main.tex')
for p in (paper/'images').glob('*.png'): add(p,'paper/images/'+p.name)
for p in (paper/'review-20261030').glob('*'):
    if p.is_file(): add(p,'review/'+p.name)
for directory in ['research/routing-pilot-v1','outputs/routing-evaluation-20261025-provisional','outputs/ambiguity-evaluation-20261025-provisional','outputs/routing-ai-review-20261025']:
    for p in (root/directory).glob('*'):
        if p.suffix in {'.json','.csv','.txt'}: add(p)
for p in (root/'outputs/access-terminal-pilot-20261025/run-04').rglob('*'):
    if p.is_file() and p.suffix in {'.json','.csv','.py','.log','.txt'}: add(p)
add(root/'outputs/access-terminal-pilot-20261025/summary.json')
add(root/'paper-routing-study/USABILITY-NOTES-20261028.txt','usability/anonymized-notes.txt')
for name in ['evaluate_routing_pilot.py','evaluate_ambiguity_pilot.py','run_access_terminal_pilot.py','review_paper_20261030.py']:
    add(root/'scripts'/name,'current-scripts/'+name)
audit_path=paper/'review-20261030/audit.json'
audit=json.loads(audit_path.read_text())
audit['source_sha256']=hashlib.sha256((paper/'main.tex').read_bytes()).hexdigest()
audit['desktop_compile_success']=True
audit['desktop_page_limit_15_checked']=True
audit_path.write_text(json.dumps(audit,indent=2),encoding='utf8')
manifest=[dict(file=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for name,p in sorted(paths.items())]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name,p in sorted(paths.items()): z.write(p,name)
    z.writestr('manifest-sha256.json',json.dumps(manifest,indent=2))
    z.writestr('READ-ME.txt',
      'Research evidence bundle, 30 October 2026.\n'
      'paper/main.tex is the revised manuscript; llncs.cls must be supplied by the official template/editor.\n'
      'Study 3 canonical evidence is run-04; source_snapshots contains the saved tested files.\n'
      'current-scripts are workspace copies, not a claim that every file matches its historical frozen hash.\n'
      'Model artifacts are NOT included; locate the original model by the recorded version/hash before reproducing inference.\n'
      'References and action labels remain AI-authored/provisional; no agency validation or participant consent is inferred.\n'
      'See review/reviewer-feedback.md for limitations and remaining work.\n')
print(f'Packaged {len(paths)} files: {archive}')
