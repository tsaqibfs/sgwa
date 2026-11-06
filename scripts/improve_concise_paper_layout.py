"""Improve readability in the 11-page Overleaf PDF's source."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'paper-routing-15-pages'
file=PROJECT/'main.tex'
tex=file.read_text(encoding='utf-8-sig')
history=PROJECT/'revision-history'
history.mkdir(exist_ok=True)
(history/'before-figures-tables-20261028.tex').write_text(tex,encoding='utf-8')
tex=tex.replace(r'\usepackage{array}',r'\usepackage{array}'+'\n'+r'\usepackage{tabularx}'+'\n'+r'\newcolumntype{Y}{>{\raggedright\arraybackslash}X}')
tex=tex.replace('The screenshots in Fig.~\\ref{fig:prototype} document a synthetic demonstration, not the usability sessions.',
                'Figures~\\ref{fig:prototype}--\\ref{fig:prototype-final} document a synthetic demonstration, not the usability sessions.')

old=re.search(r'\\begin\{figure\}\[!htbp\]\\centering\s*\\begin\{minipage\}.*?\\label\{fig:prototype\}\\end\{figure\}',tex,re.S)
assert old and old.group().count('includegraphics')==4
figures=r'''\begin{figure}[!htbp]\centering
\includegraphics[width=\linewidth]{images/prototype-01-citizen-form.png}
\caption{Citizen form showing a simulated request for information about a lost identity card (KTP).}\label{fig:prototype}
\end{figure}

\begin{figure}[!htbp]\centering
\includegraphics[width=\linewidth]{images/prototype-03-admin-assignment.png}
\caption{Administrator review: civil registration is selected before forwarding the request. Selecting a destination alone does not create the departmental task.}\label{fig:prototype-admin}
\end{figure}

\begin{figure}[!htbp]\centering
\includegraphics[width=\linewidth]{images/prototype-04-department-processing.png}
\caption{Departmental staff view showing the request being processed and a completion note prepared for the decision.}\label{fig:prototype-staff}
\end{figure}

\begin{figure}[!htbp]\centering
\includegraphics[width=\linewidth]{images/prototype-05-citizen-result.png}
\caption{Citizen view of the completed demonstration, including the departmental decision and request history. This illustrates an information-request workflow, not issuance of an identity document.}\label{fig:prototype-final}
\end{figure}
\FloatBarrier'''
tex=tex[:old.start()]+figures+tex[old.end():]

def replace_table(label, change):
    global tex
    blocks=list(re.finditer(r'\\begin\{table\}\[!htbp\].*?\\end\{table\}',tex,re.S))
    matches=[m for m in blocks if r'\label{'+label+'}' in m.group()]
    assert len(matches)==1, label
    m=matches[0]
    block=change(m.group())
    tex=tex[:m.start()]+block+tex[m.end():]

def related(s):
    s=s.replace(r'\footnotesize',r'\footnotesize\setlength{\tabcolsep}{4pt}',1)
    s=s.replace(r'\begin{tabular}{p{0.20\linewidth}p{0.31\linewidth}p{0.37\linewidth}}',r'\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{.18\linewidth}YY@{}}')
    return s.replace(r'\end{tabular}',r'\end{tabularx}')

def category(s):
    s=s.replace(r'\begin{tabular}{r p{.48\linewidth} r r r}',r'\begin{tabularx}{\linewidth}{@{}r Y r r r@{}}')
    return s.replace(r'\end{tabular}',r'\end{tabularx}')

def ambiguity(s):
    s=s.replace(r'\footnotesize',r'\footnotesize\setlength{\tabcolsep}{4pt}',1)
    s=s.replace(r'\begin{tabular}{p{.44\linewidth}rrr}',r'\begin{tabularx}{\linewidth}{@{}Y r r r@{}}')
    s=s.replace('Baseline forced & Baseline review & Policy review',r'\shortstack{Baseline\\forced} & \shortstack{Baseline\\review} & \shortstack{Policy\\review}')
    return s.replace(r'\end{tabular}',r'\end{tabularx}')

def access(s):
    s=s.replace(r'\begin{tabular}{p{.11\linewidth}p{.33\linewidth}p{.27\linewidth}p{.16\linewidth}}',r'\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{.12\linewidth}Y >{\raggedright\arraybackslash}p{.14\linewidth} >{\raggedright\arraybackslash}p{.18\linewidth}@{}}')
    s=s.replace('Expected/actual & Protected data',r'\shortstack[l]{Expected/\\actual} & Protected data')
    return s.replace(r'\end{tabular}',r'\end{tabularx}')

def usability(s):
    s=s.replace(r'\footnotesize',r'\footnotesize\setlength{\tabcolsep}{4pt}',1)
    s=s.replace(r'\begin{tabular}{l l l p{.50\linewidth}}',r'\begin{tabularx}{\linewidth}{@{}l l l Y@{}}')
    return s.replace(r'\end{tabular}',r'\end{tabularx}')

for label,fn in [('tab:related',related),('tab:class',category),('tab:ambiguity',ambiguity),('tab:access',access),('tab:usability',usability)]:
    replace_table(label,fn)
assert tex.count(r'\begin{tabularx}')==5 and tex.count(r'\end{tabularx}')==5
assert tex.count(r'\includegraphics')==4 and 'minipage' not in tex
file.write_text(tex,encoding='utf-8')
print('Updated 4 separate full-width figures and 5 flexible-width tables.')
