"""Condense wording while restoring all tables/figures from user-supplied manuscript."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'paper-routing-15-pages/main.tex'
source=Path('C:/Users/Lenovo/.codex/attachments/0fc3c7e6-c83a-4ba6-802f-a8d950e8d47b/Pasted text.txt').read_text(encoding='utf-8-sig')
text=target.read_text(encoding='utf-8-sig')
backup=ROOT/'paper-routing-15-pages/revision-history'
backup.mkdir(exist_ok=True)
(backup/'before-restoring-complete-data.tex').write_text(text,encoding='utf-8')

def block(src,kind,label):
    pattern=rf'\\begin\{{{kind}\}}(?:\[[^]]*\])?.*?\\end\{{{kind}\}}'
    found=[m.group() for m in re.finditer(pattern,src,re.S) if r'\label{'+label+'}' in m.group()]
    assert len(found)==1,(kind,label,len(found))
    return found[0]

def swap(kind,old,new):
    global text
    before=block(text,kind,old)
    assert text.count(before)==1
    text=text.replace(before,new,1)

def table(label):
    return block(source,'table',label)

def figure(label):
    return block(source,'figure',label)

# Use the complete original related-work table, but allow its columns to wrap.
related=block(source,'longtable','tab:related-comparison')
related=(r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}'+'\n'+related+'\n'+r'\endgroup')
swap('table','tab:related',related)
text=text.replace(r'\ref{tab:related}',r'\ref{tab:related-comparison}')

# Original complete 25-class and 20-case ambiguity tables replace shortened tables.
swap('table','tab:class',table('tab:perclass'))
text=text.replace(r'\ref{tab:class}',r'\ref{tab:perclass}')
swap('table','tab:ambiguity',table('tab:ambiguity'))
swap('table','tab:access',table('tab:access'))
swap('table','tab:usability',table('tab:usability'))

# Reinstate all 10 case rows instead of the abbreviated 6; preserve exact data.
endpoint=table('tab:endpoint-cases')
endpoint=endpoint.replace(r'\begin{tabular}{p{0.07\linewidth}p{0.25\linewidth}p{0.29\linewidth}p{0.12\linewidth}p{0.16\linewidth}}',
    r'\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{.06\linewidth}Y Y >{\raggedright\arraybackslash}p{.12\linewidth} >{\raggedright\arraybackslash}p{.15\linewidth}@{}}')
endpoint=endpoint.replace(r'\end{tabular}',r'\end{tabularx}')
assert r'\begin{tabularx}' in endpoint
marker=r'\subsection{Exploratory usability and limitations}'
assert text.count(marker)==1
text=text.replace(marker,table('tab:failures')+'\n\n'+endpoint+'\n\n'+marker,1)

# The experimental-condition table and both omitted workflow diagrams retain their original content.
marker=r'\subsection{Experimental design}'
assert text.count(marker)==1
text=text.replace(marker,figure('fig:routing-decision')+'\n\n'+table('tab:conditions')+'\n\n'+marker,1)
marker=r'\textbf{Study 1.}'
assert text.count(marker)==1
text=text.replace(marker,figure('fig:test-flow')+'\n\n'+marker,1)

# Keep every screenshot from the 26-page version, one per figure, at 90% text width.
for old,new in [('fig:prototype','fig:citizen-form'),('fig:prototype-admin','fig:admin-assignment'),('fig:prototype-staff','fig:department-processing'),('fig:prototype-final','fig:citizen-result')]:
    swap('figure',old,figure(new))
insert=figure('fig:submitted-request')
text=text.replace(figure('fig:citizen-form'),figure('fig:citizen-form')+'\n\n'+insert,1)
for name in ['01-citizen-form','02-submitted-request','03-admin-assignment','04-department-processing','05-citizen-result']:
    text=text.replace(r'\includegraphics[width=\linewidth]{images/prototype-'+name+'.png}',r'\includegraphics[width=.90\linewidth]{images/prototype-'+name+'.png}')
text=text.replace(r'Figures~\ref{fig:prototype}--\ref{fig:prototype-final}',r'Figures~\ref{fig:citizen-form}--\ref{fig:citizen-result}')

# Reinstate both charts and the exact 625 cells from the original confusion matrix.
swap('figure','fig:cm',figure('fig:confusion'))
text=text.replace(r'\ref{fig:cm}',r'\ref{fig:confusion}')
matrix=figure('fig:confusion')
text=text.replace(matrix,matrix.replace('width=\\linewidth,height=\\linewidth','width=7.0cm,height=7.0cm').replace('mark size=2.9pt','mark size=2.0pt'),1)
text=text.replace(r'\subsection{Study 2: ambiguity and comparison}',figure('fig:f1')+'\n\n'+r'\subsection{Study 2: ambiguity and comparison}',1)
text=text.replace(r'\subsection{Study 3: access and terminal-state cases}',figure('fig:ambiguity')+'\n\n'+r'\subsection{Study 3: access and terminal-state cases}',1)
text=text.replace('width=\\linewidth,height=6cm','width=\\linewidth,height=4.6cm').replace('width=\\linewidth,height=5.8cm','width=\\linewidth,height=4.6cm')

# Preserve other recorded results that occurred only in the source narrative.
text=text.replace('Of 500 references, 33 were marked conditional;',
    'Of 500 references, 467 were marked semantically consistent and 33 conditional;')
text=text.replace('These cautions did not lead to exclusions or relabeling.',
    'No proposed reference label was changed or excluded after review. The 2021--2026 source checks covered seven official pages, not individual expert validation of all cases.')
text=text.replace('All five participants were recorded as independent.',
    'All five participants were recorded as independent (5/5); this is an overall session outcome, not a task-by-task completion rate.')
text=text.replace('and one reported an incorrect category for a wet family-card request.',
    'and one reported an incorrect category for a wet family-card request (not reproduced from logs).')
text=text.replace(r'\begin{document}'+'\n'+r'\raggedbottom',r'\begin{document}'+'\n'+r'\raggedbottom'+'\n'+r'\setlength{\textfloatsep}{8pt plus 2pt minus 2pt}'+'\n'+r'\setlength{\intextsep}{7pt plus 2pt minus 2pt}')

# Tables and figures are preserved separately and readable; reduce diagram height, not the font size.
text=text.replace('node distance=5mm,','node distance=3mm,').replace('node distance=6mm,','node distance=3mm,').replace('node distance=7mm and 5mm,','node distance=3mm and 5mm,')
text=text.replace('inner sep=5pt','inner sep=3pt')

# Check original table rows and figure payloads before touching the open document.
for label in ['tab:related-comparison','tab:conditions','tab:perclass','tab:ambiguity','tab:access','tab:failures','tab:endpoint-cases','tab:usability']:
    assert r'\label{'+label+'}' in text,label
for label in ['fig:architecture','fig:routing-decision','fig:test-flow','fig:citizen-form','fig:submitted-request','fig:admin-assignment','fig:department-processing','fig:citizen-result','fig:f1','fig:ambiguity','fig:confusion']:
    assert r'\label{'+label+'}' in text,label
assert len(re.findall(r'\\bibitem\{',text))==15
refs=set(re.findall(r'\\ref\{([^}]+)\}',text));labels=re.findall(r'\\label\{([^}]+)\}',text)
assert refs<=set(labels),refs-set(labels)
assert len(labels)==len(set(labels))
target.write_text(text,encoding='utf-8')
print('Restored all 8 original data tables and 11 original figures, plus all 15 references; condensed body text retained.')
