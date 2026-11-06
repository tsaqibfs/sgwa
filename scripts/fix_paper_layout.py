"""Keep results and figures next to their discussion in the LLNCS manuscript."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper-routing-study'
path=P/'main.tex'
tex=path.read_text(encoding='utf-8-sig')
assert r'\usepackage{float}' not in tex, 'Layout patch already applied'
(P/'revision-history/pre-layout-20261027.tex').write_text(tex,encoding='utf-8')
tex=tex.replace(r'\usepackage{longtable}',r'\usepackage{longtable}'+'\n'+r'\usepackage{float}'+'\n'+r'\usepackage[section]{placeins}')
tex=tex.replace(r'\usepackage{array}',r'\usepackage{array}'+'\n'+r'\setlength{\emergencystretch}{1em}')
tex=re.sub(r'\\begin\{(figure|table)\}\[[^]]*\]',lambda m:r'\begin{'+m[1]+'}[H]',tex)

def compact_table(block):
    # These tables fit a page; longtable unnecessarily split their small row sets.
    m=re.search(r'\\begin\{longtable\}(\{[^\n]+\})\n(.*?)\\end\{longtable\}',block,re.S)
    assert m
    columns,body=m.groups()
    caption=re.search(r'\\caption\{.*?\\label\{[^}]+\}\\\\',body,re.S)
    assert caption
    cap=caption[0][:-2]
    body=body.replace(caption[0],'',1)
    if r'\endfirsthead' in body:
        first,rest=body.split(r'\endfirsthead',1)
        _,rest=rest.split(r'\endhead',1)
        body=first+rest
    return r'\begin{table}[H]'+'\n'+r'\centering\footnotesize'+'\n'+cap+'\n'+r'\begin{tabular}'+columns+'\n'+body.strip()+'\n'+r'\end{tabular}'+'\n'+r'\end{table}'

# Convert only per-category and endpoint tables, preserving their data and captions.
for label in ['tab:perclass','tab:endpoint-cases']:
    pattern=r'\\begingroup\\scriptsize\s*(?:\\setlength\{\\tabcolsep\}\{3pt\}\s*)?\\begin\{longtable\}.*?\\end\{longtable\}\s*\\endgroup'
    matches=[m for m in re.finditer(pattern,tex,re.S) if r'\label{'+label+'}' in m[0]]
    # A greedy cross-table match is avoided by restricting to the nearest longtable.
    if len(matches)!=1:
        raise ValueError(f'Cannot locate table {label}')
    match=matches[0]
    assert match[0].count(r'\begin{longtable}')==1, 'Cross-table match'
    tex=tex[:match.start()]+compact_table(match[0])+tex[match.end():]

# Improve dense prose tables without scaling the fonts smaller.
tex=tex.replace(r'p{0.16\linewidth}p{0.35\linewidth}p{0.39\linewidth}',
                r'>{\raggedright\arraybackslash}p{0.14\linewidth}>{\raggedright\arraybackslash}p{0.33\linewidth}>{\raggedright\arraybackslash}p{0.40\linewidth}')
tex=tex.replace(r'\label{tab:failures}\centering\scriptsize',r'\label{tab:failures}\centering\footnotesize')
# Endpoint headings wrap within fixed-width columns instead of running together.
tex=tex.replace('Expected/actual & Table effect',r'Expected / actual & Table effect')
tex=tex.replace(r'\begingroup\scriptsize\setlength{\tabcolsep}{3pt}',r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}')
tex=re.sub(r'(?<!>)p\{(0\.(?:19|23|24))\\linewidth\}',r'>{\raggedright\arraybackslash}p{\1\\linewidth}',tex)
# Prevent a graph from outliving Results and the appendix from entering References.
tex=tex.replace(r'\appendix',r'\FloatBarrier'+'\n'+r'\clearpage'+'\n'+r'\appendix',1)
tex=tex.replace(r'\begin{thebibliography}',r'\FloatBarrier'+'\n'+r'\clearpage'+'\n'+r'\begin{thebibliography}',1)
path.write_text(tex,encoding='utf-8')
(P/'LAYOUT-REVIEW-20261027.txt').write_text('''Review of the user-supplied 23-page Overleaf PDF

Confirmed in rendered PDF:
- Figures 9 and 10 were deferred to page 22, after References (pages 20-21),
  although discussed in Results (pages 16-17).
- Table 3 started with six category rows on page 15 and continued on page 16.
- Table 7 started with two endpoint rows near the bottom of page 18.
- Short floating tables appeared at page tops before their section text.
- The failure table was dense and its narrow columns visually crowded.

Source causes and corrections:
- Figure 9 used [p]; later figures queued behind it. Changed figure/table
  placement to [H] via the float package to keep each at its source location.
- Added section float barriers, and explicit boundaries before Appendix and
  References. All figures now precede References in source and cannot cross it.
- Converted the 25-category and 10-endpoint tables from breakable longtable
  to intact table/tabular blocks; kept the longer related-work longtable.
- Increased compact table text to footnotesize and made prose columns ragged
  right. Rebalanced the failure-table widths and added emergency line stretch.
- No result values, reference claims or image pixels were changed.

Tradeoff: exact source placement can leave white space when a complete figure
or table must start on the next page. This is preferable here to graphs after
the bibliography or partial short tables. Keep the LLNCS class and margins.
The full-screen screenshots contain small UI text at paper width; placement
changes do not make all interface text readable. Consider user-approved detail
crops in a later revision if greater UI legibility is required.
''',encoding='utf-8')
print('Patched float placement and two short tables; preserved all numeric evidence.')
