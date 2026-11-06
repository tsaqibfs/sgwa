"""Record reference checks against observed primary sources (not invented DOI tests)."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper-routing-study'
tex=(P/'main.tex').read_text(encoding='utf-8-sig')
sources={
'oecd2025governing':('https://www.oecd.org/en/publications/governing-with-artificial-intelligence_795de142-en.html','Official publisher page and DOI landing page checked; book/report, 2025.'),
'li2022survey':('https://eprints.whiterose.ac.uk/id/eprint/186633/','Author institutional repository and published article copy checked; ACM direct access returned 403. Final 2022 version used, not the preprint containing placeholder journal metadata.'),
'wu2022survey':('https://doi.org/10.1016/j.future.2022.05.014','Publisher-indexed title and abstract checked; later direct fetch returned 403. This is not evidence of an invalid DOI.'),
'madyatmadja2023complaints':('https://doi.org/10.3390/informatics10040084','Publisher article content and issue listing checked during review; later fetch rate-limited.'),
'majumder2025tipline':('https://aclanthology.org/2025.emnlp-main.1788/','Official proceedings title, authors, year, pages and DOI checked.'),
'zhang2021wrench':('https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/1c9ac0159c94d8d0cbedc973445af2da-Paper-round2.pdf','Official proceedings and PDF checked. Third author confirmed as Yinghao Li from PDF; landing page has a NameError metadata defect. No publisher DOI asserted. Cite final late-2021 proceedings, not September preprint.'),
'ariyana2025multilabel':('https://jpti.journals.id/index.php/jpti/article/view/796','Journal page confirms title, authors, 24 March 2025, volume 5(3), pages 615-623, and DOI.'),
'owasp2023bola':('https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/','Official 2023 technical guidance checked; not a research article; no DOI invented.'),
'lamonganmerger':('https://disperindag.lamongankab.go.id/posting/6243','Official banner refers to 2025 regulation. Underlying service article is dated 2022; the banner is not misrepresented as the publication date of that article. No DOI.'),
'he2022generate':('https://aclanthology.org/2022.tacl-1.48/','Official article record: title, all five authors, 2022, volume 10, pages 826-842, DOI checked.'),
'li2023synthetic':('https://aclanthology.org/2023.emnlp-main.647/','Official proceedings: title, four authors, December 2023, pages 10443-10461, DOI checked.'),
'ramesh2025synthtexteval':('https://aclanthology.org/2025.emnlp-demos.35/','Official proceedings: title, seven authors, 2025, pages 487-499, DOI checked.'),
'kapoor2023leakage':('https://www.cell.com/patterns/fulltext/S2666-3899(23)00159-9','Publisher-indexed title/authors and article identifier checked. Direct DOI fetch returned 403; no successful direct retrieval is claimed. Corroborating author source: https://reproducible.cs.princeton.edu/'),
'silva2023calibration':('https://link.springer.com/article/10.1007/s10994-023-06336-7','Publisher page: six authors, publication 16 May 2023, volume 112, pages 3211-3260, DOI checked.'),
'vaccaro2024combination':('https://www.nature.com/articles/s41562-024-02024-1','Publisher page: three authors, publication 28 October 2024, volume 8, pages 2293-2303, DOI checked.'),
}
entries=[]
for key,body in re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})',tex,re.S):
    url,note=sources[key]
    dois=re.findall(r'\\doi\{([^}]+)\}',body)
    entries.append({'key':key,'doi':dois[0] if dois else None,'primary_source':url,
                    'check_note':note,'checked_date':'2026-10-27',
                    'bibitem_sha256':hashlib.sha256(body.strip().encode()).hexdigest()})
assert len(entries)==15 and sum(bool(e['doi']) for e in entries)==12
audit={'reference_count':15,'with_doi':12,'url_only':3,'new_references':6,
       'scope':'Metadata, availability and relevance check against primary sources; not a systematic literature review or a claim that every DOI fetch succeeded.',
       'date_policy':'New research references are 2022-2025. Existing WRENCH uses final late-2021 proceedings; verify the submission venue interpretation of the five-year window.',
       'entries':entries}
(P/'reference-audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
print('15 reference entries recorded: 12 DOI-bearing, 3 official URL-only sources.')
