"""Restore flexible floats without stretching heading/paragraph vertical space."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper-routing-study'
main=P/'main.tex'
tex=main.read_text(encoding='utf-8-sig')
assert r'\raggedbottom' not in tex, 'Spacing revision already present'
(P/'revision-history/pre-balanced-spacing-20261027.tex').write_text(tex,encoding='utf-8')
tex=tex.replace(r'\begin{document}',r'\begin{document}'+'\n'+r'\raggedbottom',1)
tex=re.sub(r'\\begin\{(figure|table)\}\[H\]',lambda m:r'\begin{'+m[1]+'}[!htbp]',tex)
tex=tex.replace(r'\usepackage{float}'+'\n','')
tex=tex.replace(r'\clearpage',r'\FloatBarrier')
tex=re.sub(r'(\\FloatBarrier\s*){2,}',lambda _: r'\FloatBarrier'+'\n',tex)
# Limit figure drift to the relevant results study, rather than pinning each object.
start=tex.index(r'\section{Results and discussion}')
before,results=tex[:start],tex[start:]
results=results.replace(r'\subsection{',r'\FloatBarrier'+'\n'+r'\subsection{')
tex=before+results
main.write_text(tex,encoding='utf-8')
(P/'SPACING-REVIEW-20261027.txt').write_text('''Balanced spacing revision after reviewing the 26-page exported PDF

Observed: pages 7 and 10 show very large gaps around section headings and
paragraphs; page 17 has an intact category table followed by unused space.
The previous universal [H] setting made floats too rigid, while page-height
justification stretched the available vertical glue.

Changes:
- Added raggedbottom after begin{document}: preserve natural heading and
  paragraph spacing instead of stretching it to fill the page.
- Restored flexible [!htbp] placement for all figures and tables.
- Retained section barriers and added barriers between Results subsections,
  so F1 and fallback figures cannot drift beyond their study discussion.
- Replaced explicit clearpage commands with FloatBarrier. These drain pending
  floats when necessary without always starting a new page.
- Kept the two result tables intact; no change to LLNCS margins, font family,
  class, screenshot pixels, or numerical results.

Some space at a page bottom remains normal when an intact table cannot fit.
This revision targets excessive internal gaps, not equal page-bottom heights.
The prior LAYOUT-REVIEW file describes the earlier intermediate revision;
this spacing revision supersedes its universal [H] strategy.
Final Overleaf pagination must be checked in the newly exported PDF.
''',encoding='utf-8')
print('Balanced spacing applied: raggedbottom, flexible floats, study barriers; no forced clearpage.')
