"""Apply the supervisor's presentation revisions without changing pilot results."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'paper-routing-study'
main = PROJECT / 'main.tex'
tex = main.read_text(encoding='utf-8-sig')
assert 'sec:research-gap' not in tex, 'Revision already applied; edit the manuscript in place.'
(PROJECT / 'revision-history').mkdir(exist_ok=True)
(PROJECT / 'revision-history/pre-supervisor-20261027.tex').write_text(tex, encoding='utf-8')
tex = tex.replace(r'\pgfplotsset{compat=1.18}', r'\pgfplotsset{compat=1.18}'+'\n'+r'\usetikzlibrary{arrows.meta,positioning,shapes.geometric}')

RELATED = r'''
\subsection{Comparison and research gap}\label{sec:research-gap}
Table~\ref{tab:related-comparison} identifies the methodological basis of the present study. The extension is a joint prototype evaluation of category recommendations, action-level fallback, and request-specific authority. It does not claim that earlier systems lacked access controls; those controls are outside the classification results compared here. No performance ranking across their different datasets is attempted.

\begingroup\scriptsize\setlength{\tabcolsep}{3pt}
\begin{longtable}{p{0.19\linewidth}p{0.23\linewidth}p{0.24\linewidth}p{0.24\linewidth}}
\caption{Related work and the basis for SGWA's evaluation.}\label{tab:related-comparison}\\
\toprule Study & Categories and label/data basis & Rules or ambiguity handling & Basis and boundary for SGWA\\\midrule\endfirsthead
\toprule Study & Categories and label/data basis & Rules or ambiguity handling & Basis and boundary for SGWA\\\midrule\endhead
Madyatmadja et al.~\cite{madyatmadja2023complaints} & LAKSA complaint categories; officer-annotated records & Supervised classifiers compared, rather than the SGWA keyword heuristic & Motivates domain-informed labels and category-level error analysis; SGWA currently lacks such label validation.\\
Majumder et al.~\cite{majumder2025tipline} & EPA citizen tips and enforcement divisions & Relevance screening followed by LLM-assisted destination routing & Motivates separating unsupported inputs from destination selection; agency scope and model differ.\\
Zhang et al.~\cite{zhang2021wrench} & 22 benchmark datasets with weak supervision & Noisy labeling functions can conflict or abstain & Motivates documenting heuristic sources and abstention; not a government workflow benchmark.\\
Ariyana et al.~\cite{ariyana2025multilabel} & Multi-label Wargaku complaints & Binary Relevance, Classifier Chains, and Label Powerset & Motivates an explicit output definition; SGWA's pilot predicts one primary category only.\\
Wu et al.~\cite{wu2022survey}; Vaccaro et al.~\cite{vaccaro2024combination} & Survey and meta-analysis across human--AI settings & Human intervention and combination outcomes & Motivates measuring actual assistance and decisions; a review queue alone does not establish human--AI benefit.\\
He et al.~\cite{he2022generate}; Li et al.~\cite{li2023synthetic} & Generated text and synthetic classification datasets & Generation/annotation strategies; task-dependent limitations & Motivates reporting synthetic provenance; generated labels do not replace jurisdiction review.\\
Present study & 25 prototype categories; 500 balanced texts; 25 action scenarios & Fixed keyword comparator versus mandatory-review policy & Adds a separate 61-case access/state pilot; routing claims remain provisional.\\
\bottomrule\end{longtable}\endgroup

Additional literature informs interpretation rather than supplying a directly comparable routing score. Silva Filho et al.~\cite{silva2023calibration} distinguish calibrated probabilities from unverified confidence scores. Kapoor and Narayanan~\cite{kapoor2023leakage} document how leakage undermines evaluation; therefore, exact deduplication is reported without asserting semantic independence. Ramesh et al.~\cite{ramesh2025synthtexteval} frame synthetic-text assessment across multiple dimensions, including distributional and domain considerations. These works support explicit limits on a synthetic pilot's external validity. Human--AI combinations also require empirical evaluation rather than an assumption that adding review improves outcomes~\cite{vaccaro2024combination}.

'''
tex = tex.replace(r'\section{Research methodology}', RELATED + r'\section{Research methodology}',1)

METHOD = r'''
\subsection{System implementation and reproducible text pipeline}\label{sec:pipeline}
The implementation consists of a React/TypeScript client, a Python FastAPI API with SQLAlchemy, MySQL persistence, and an SLA worker. Figure~\ref{fig:architecture} separates those components; Fig.~\ref{fig:routing-decision} shows the assignment decision. Section~\ref{sec:prototype} documents their user interfaces. The research experiments use the frozen model and saved test harness, not screenshots as quantitative evidence.

For inference, the title and description are concatenated with one space. The recorded \texttt{id-v1} normalizer applies Unicode NFKC normalization, lowercasing, a small whole-token alias dictionary, and whitespace collapse. For example, \texttt{jln}, \texttt{bnyk}, and \texttt{lampmer} become \texttt{jalan}, \texttt{banyak}, and \texttt{lampu merah}. This is limited normalization, not a general typo corrector, stemmer, or location-recognition model. The pipeline uses word unigram/bigram TF-IDF with sublinear term frequency and logistic regression with $C=4.0$, a maximum of 1,000 iterations, and random seed 42. Configuration evidence is preserved with the paper package. These settings describe the implementation; they are not a new hyperparameter search on the 500 pilot texts.

Synthetic text can support NLP development~\cite{he2022generate}, but its usefulness varies with the task and instance characteristics~\cite{li2023synthetic}. Accordingly, generating a balanced corpus is not treated as establishing a representative test population. Scores from \texttt{predict\_proba} are recorded without a calibration claim; calibration requires separate assessment~\cite{silva2023calibration}.

\subsection{Sequence of the three experiments}\label{sec:test-flow}
Figure~\ref{fig:test-flow} summarizes the executed sequence. First, the input and reference files and the comparator definition were frozen with provenance and hashes. Next, Studies~1 and~2 generated recommendations and policy outcomes without creating citizen requests. Study~3 used separate API fixtures with case-specific expected outcomes. Finally, saved outputs were aggregated into the category table, action-condition table, access matrix, and representative failure analysis. No participant data enter this sequence. Human domain review remains outstanding; freezing proposed labels before inference does not make those labels expert-validated.

\begin{figure}[htbp]\centering
\begin{tikzpicture}[node distance=5mm,
stage/.style={draw,rounded corners=1pt,align=center,text width=9.1cm,font=\small,inner sep=5pt},
flow/.style={-{Latex[length=2mm]},thick}]
\node[stage] (freeze) {Freeze inputs, proposed references, comparator and configuration\\Record provenance and hashes; retain unvalidated-label status};
\node[stage,below=of freeze] (s1) {Study 1: infer 500 texts (25 categories $\times$ 20)\\Compare top categories; compute per-class metrics and confusion matrix};
\node[stage,below=of s1] (s2) {Study 2: apply both methods to 20 ambiguity cases + 5 controls\\Compare forced assignments, acceptable fallback and control handling};
\node[stage,below=of s2] (s3) {Study 3: prepare identities and requests in isolated MySQL\\Snapshot protected data $\to$ call endpoint $\to$ compare status and data};
\node[stage,below=of s3] (analysis) {Analyze disagreements, policy tradeoffs and access outcomes\\Preserve logs; report limits; keep pending usability separate};
\draw[flow] (freeze)--(s1);\draw[flow] (s1)--(s2);\draw[flow] (s2)--(s3);\draw[flow] (s3)--(analysis);
\end{tikzpicture}
\caption{Executed experiment flow. The offline routing pilots and the API access pilot use different units of observation and do not establish end-to-end field performance.}\label{fig:test-flow}
\end{figure}

'''
tex = tex.replace(r'\subsection{Study 1: balanced category recommendation pilot}', METHOD+r'\subsection{Study 1: balanced category recommendation pilot}',1)

ARCH = r'''\begin{figure}[htbp]\centering
\begin{tikzpicture}[node distance=7mm and 5mm,
component/.style={draw,rounded corners=1pt,align=center,text width=8.8cm,font=\small,inner sep=5pt},
flow/.style={-{Latex[length=2mm]},thick}]
\node[component] (web) {React/TypeScript web client\\Citizen submission/results $\mid$ administrator review $\mid$ departmental tasks};
\node[component,below=of web] (api) {Python FastAPI application\\Authentication, ownership/assignment checks, status and version guards};
\node[component,below=of api] (services) {Application services\\TF-IDF/logistic regression $\mid$ category mapping and review policy\\Workflows, attachments, results, notifications and audit history};
\node[component,below=of services] (db) {SQLAlchemy $\longleftrightarrow$ MySQL\\Persistent requests, assignments, events and supporting records};
\node[component,below=of db] (worker) {Background SLA worker\\Checks workflow deadlines through the application/database layer};
\draw[flow] (web)--node[right,font=\scriptsize]{API requests/responses} (api);
\draw[flow] (api)--(services);\draw[flow] (services)--(db);\draw[flow] (worker)--(db);
\end{tikzpicture}
\caption{SGWA components and server-side enforcement. Authentication and request-specific authority apply before protected operations; a classifier score does not itself grant access.}
\label{fig:architecture}
\end{figure}'''
tex = re.sub(r'\\begin\{figure\}\[t\].*?\\label\{fig:architecture\}\s*\\end\{figure\}',lambda _:ARCH,tex,count=1,flags=re.S)

DECISION = r'''
\begin{figure}[htbp]\centering
\begin{tikzpicture}[node distance=6mm,
routestep/.style={draw,align=center,text width=8.8cm,font=\small,inner sep=5pt},
flow/.style={-{Latex[length=2mm]},thick}]
\node[routestep] (input) {Citizen title + description $\to$ normalization $\to$ category and score};
\node[routestep,below=of input] (policy) {Check routing policy and active destination mapping\\Evaluated configuration: automatic routing disabled};
\node[routestep,below=of policy] (review) {Administrator review required for every input\\Inspect context; record note; select primary/supporting departments};
\node[routestep,below=of review] (assign) {Forward action persists department task(s)\\A direct final decision is a separate operation};
\node[routestep,below=of assign] (staff) {Assigned staff access their authorized task\\Process and record decision under state/version guards};
\node[routestep,below=of staff] (result) {Citizen reads their own status, history and result};
\draw[flow] (input)--(policy);\draw[flow] (policy)--(review);\draw[flow] (review)--(assign);\draw[flow] (assign)--(staff);\draw[flow] (staff)--(result);
\end{tikzpicture}
\caption{Operational assignment flow under the evaluated mandatory-review policy. The diagram does not imply automated clarification, autonomous correction, or an enabled automatic-routing branch.}\label{fig:routing-decision}
\end{figure}

'''
tex = tex.replace(r'\subsection{Prototype demonstration and screenshot evidence}',DECISION+r'\subsection{Prototype demonstration and screenshot evidence}',1)

# Derive representative endpoint rows from saved evidence, never invent responses.
cases = {r['case_id']:r for r in csv.DictReader((PROJECT/'evidence/study-3/case-matrix.csv').open(encoding='utf-8-sig'))}
selected = ['D01','D02','D07','T32','T35','V01','M01','M02','M03','M04']
meaning = {'D01':'Unauthenticated read','D02':'Staff A reads B request',
           'D07':'Staff A changes B status','T32':'Reopen approved task','T35':'Reroute approved request',
           'V01':'Replay stale task version','M01':'Own task: start processing',
           'M02':'Own task: final approval','M03':'Admin assigns departments',
           'M04':'Own task on shared request'}
actors = {'anonymous':'Anonymous','staff_a':'Staff A','admin':'Admin'}
table_rows=[]
for key in selected:
    r=cases[key]
    endpoint=r['endpoint'].removeprefix('/api/v1')
    effect = 'Unchanged (9/9)' if r['expect_business_change']=='False' else f"Changed ({len(r['changed_tables'].split(';'))}/9)"
    table_rows.append(f"{key} & {actors[r['actor']]}: {meaning[key]} & {r['method']} \\path{{{endpoint}}} & {r['expected_http']}/{r['actual_http']} & {effect} \\\\")
ENDPOINTS = r'''
\subsection{Representative endpoint scenarios and database evidence}\label{sec:endpoint-evidence}
Table~\ref{tab:endpoint-cases} brings selected case-level evidence into the paper rather than relying solely on the aggregate pass count. Endpoint paths share the prefix \texttt{/api/v1}; numeric identifiers refer only to isolated fixtures. The expected/actual columns are HTTP status codes, not inferred permissions. A rejected case must also preserve protected data; returning an error alone is insufficient evidence of rollback or non-mutation.

\begingroup\scriptsize\setlength{\tabcolsep}{3pt}
\begin{longtable}{p{0.07\linewidth}p{0.25\linewidth}p{0.29\linewidth}p{0.12\linewidth}p{0.16\linewidth}}
\caption{Selected Study 3 scenarios from the saved case matrix. Data effects concern nine protected tables, not the entire database.}\label{tab:endpoint-cases}\\
\toprule ID & Actor and action & Endpoint (prefix omitted) & Expected/actual & Table effect\\\midrule\endfirsthead
\toprule ID & Actor and action & Endpoint (prefix omitted) & Expected/actual & Table effect\\\midrule\endhead
__ROWS__
\bottomrule\end{longtable}\endgroup

M01 changed the request, workflow, event, notification, and audit tables. M02 additionally persisted a result-document record. M03 created the assigned departmental workflow state, while M04 changed only the permitted task within a shared request according to the case assertion. For the selected rejected cases, all nine protected tables and checked fixture files remained unchanged, including request history. The complete 61-row matrix, 549 table comparisons, and final-run log remain in the evidence package. These observations establish the checked invariants, not a comprehensive security guarantee.

'''.replace('__ROWS__','\n'.join(table_rows))
tex=tex.replace(r'\subsection{Relationship to the research question and threats to validity}',ENDPOINTS+r'\subsection{Relationship to the research question and threats to validity}',1)

newrefs = r'''
\bibitem{he2022generate}
He, X., Nassar, I., Kiros, J., Haffari, G., Norouzi, M.:
Generate, annotate, and learn: NLP with synthetic text.
Transactions of the Association for Computational Linguistics \textbf{10}, 826--842 (2022).
\doi{10.1162/tacl_a_00492}

\bibitem{li2023synthetic}
Li, Z., Zhu, H., Lu, Z., Yin, M.:
Synthetic data generation with large language models for text classification: Potential and limitations.
In: Proceedings of EMNLP 2023, pp. 10443--10461. Association for Computational Linguistics (2023).
\doi{10.18653/v1/2023.emnlp-main.647}

\bibitem{ramesh2025synthtexteval}
Ramesh, K., Smolyak, D., Zhao, Z., Gandhi, N., Agarwal, R., Bjarnadottir, M.V., Field, A.:
SynthTextEval: Synthetic text data generation and evaluation for high-stakes domains.
In: Proceedings of EMNLP 2025: System Demonstrations, pp. 487--499.
Association for Computational Linguistics (2025).
\doi{10.18653/v1/2025.emnlp-demos.35}

\bibitem{kapoor2023leakage}
Kapoor, S., Narayanan, A.:
Leakage and the reproducibility crisis in machine-learning-based science.
Patterns \textbf{4}(9), 100804 (2023).
\doi{10.1016/j.patter.2023.100804}

\bibitem{silva2023calibration}
Silva Filho, T., Song, H., Perello-Nieto, M., Santos-Rodriguez, R., Kull, M., Flach, P.:
Classifier calibration: a survey on how to assess and improve predicted class probabilities.
Machine Learning \textbf{112}, 3211--3260 (2023).
\doi{10.1007/s10994-023-06336-7}

\bibitem{vaccaro2024combination}
Vaccaro, M., Almaatouq, A., Malone, T.:
When combinations of humans and AI are useful: A systematic review and meta-analysis.
Nature Human Behaviour \textbf{8}, 2293--2303 (2024).
\doi{10.1038/s41562-024-02024-1}
'''
tex=tex.replace(r'\begin{thebibliography}{9}',r'\begin{thebibliography}{15}')
tex=tex.replace(r'\end{thebibliography}',newrefs+'\n'+r'\end{thebibliography}')
tex=tex.replace(r'\url{https://openreview.net/forum?id=Q9SKS5k8io}',r'\url{https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/1c9ac0159c94d8d0cbedc973445af2da-Abstract-round2.html}')
main.write_text(tex,encoding='utf-8')
# Save the exact config sources used to explain the pipeline. Preserve existing result hashes.
for src in ['ml/text.py','ml/evaluation.py']:
    target=PROJECT/'evidence/implementation'/Path(src).name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((ROOT/src).read_bytes())
notes = '''Revisi catatan dosen, 27 Oktober 2026

Ditambahkan: tabel related work dan celah penelitian; detail normalisasi/TF-IDF/
logistic regression; diagram komponen; alur keputusan mandatory review; alur
tiga eksperimen; sepuluh contoh endpoint dari log Uji 3 beserta perubahan tabel;
enam referensi relevan (total 15, 12 memiliki DOI, tiga memakai URL resmi).

Hasil uji tidak berubah. Tidak ada retraining, pengujian baru, atau data usability
yang dibuat. Semua hasil routing tetap provisional; semua 500 input ditangani
policy manual review, bukan 449 assignment otomatis berhasil. Uji 2 bukan bukti
detektor ambiguitas yang mengalahkan semua aturan. Judul kerja dosen tetap
dipertahankan dan perlu dibahas jika ingin menyelaraskan cakupan rule-based.

Tabel endpoint diturunkan langsung dari evidence/study-3/case-matrix.csv.
Riwayat naskah sebelum revisi disimpan pada revision-history/.
Konfigurasi sumber untuk uraian pipeline disalin pada evidence/implementation/.
Metadata audit referensi dan sumber pemeriksaannya ada pada reference-audit.json.
Kompilasi PDF serta hasil usability masih harus diverifikasi/dilengkapi.
'''
(PROJECT/'REVISION-20261027.txt').write_text(notes,encoding='utf-8')
print(f'Updated manuscript: {len(tex)} characters; {len(selected)} endpoint cases; 15 references.')

