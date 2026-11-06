"""Prepare an LLNCS manuscript from frozen pilot evidence; never rerun experiments."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\Lenovo\.codex\attachments\eb5b902c-aeeb-4d43-bfcc-50a2d0ce00c7\Pasted text.txt')
OUT = ROOT / '.superpowers' / 'paper-preparation'
OUT.mkdir(parents=True, exist_ok=True)
original = SOURCE.read_text(encoding='utf-8-sig')
related = original.split(r'\section{Related Work}', 1)[1].split(r'\section{Research Methodology}', 1)[0]
related = related.replace('Any keyword-based\nbaseline introduced into the study must therefore have separately\ndocumented rules and test cases.', 'The keyword comparator in this study therefore has separately\ndocumented rules and frozen test cases.')
bib = original.split(r'\begin{thebibliography}{8}', 1)[1].split(r'\end{thebibliography}', 1)[0]
rows = list(csv.DictReader((ROOT / 'outputs/routing-evaluation-20261025-provisional/per_class.csv').open(encoding='utf-8-sig')))
names = [
    'Disaster management', 'Population and civil registration',
    'Archives and libraries', 'Health', 'Communication and informatics',
    'Cooperatives and micro-enterprises', 'Environment', 'Food and agriculture',
    'Tourism and culture', 'Community and village empowerment',
    'Women empowerment and child protection', 'Youth and sports', 'Education',
    'Population control and family planning', 'Transportation', 'Fisheries',
    'Industry and trade', 'Investment and integrated licensing',
    'Housing, settlements and public facilities', 'Livestock and animal health',
    'Public works: roads', 'Public works: water resources',
    'Public order enforcement', 'Social services', 'Manpower',
]
table_rows = '\n'.join(
    f"{i+1:02d} & {names[i]} & 20 & {100*float(r['precision']):.1f} & {100*float(r['recall']):.1f} & {100*float(r['f1-score']):.1f} \\\\"
    for i, r in enumerate(rows)
)
f1coords = ' '.join(f"({i+1},{100*float(r['f1-score']):.6f})" for i,r in enumerate(rows))
cm = list(csv.reader((ROOT / 'outputs/routing-evaluation-20261025-provisional/confusion_matrix.csv').open(encoding='utf-8-sig')))
cmcoords = '\n'.join(f'({j},{i}) [{int(value)}]' for i,row in enumerate(cm[1:],1) for j,value in enumerate(row[1:],1))

tex = r'''\documentclass[runningheads]{llncs}
\usepackage[T1]{fontenc}
\usepackage{newtxtext}
\usepackage[varvw]{newtxmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage[hidelinks]{hyperref}
\begin{document}
\title{Evaluating Rule-Based Request Routing and Departmental Access Isolation in a Public Service Workflow}
\titlerunning{Request routing and departmental access isolation}
\author{Tsaqib Fadhlurrahman Soka \and Muhammad Firman Saputra}
\authorrunning{T. F. Soka and M. F. Saputra}
\institute{Electronic Engineering Polytechnic Institute of Surabaya, Surabaya, Indonesia\\
\email{humas@pens.ac.id}\\\url{https://it.pens.ac.id/}}
\maketitle

\begin{abstract}
Public service requests require an appropriate departmental destination and access boundaries that follow responsibility. This study evaluates these concerns in Smart Government Workflow Automation (SGWA), a web prototype with 25 service categories. Its pipeline separates TF-IDF and logistic regression recommendations, rule-based departmental mapping, manual review, and request-specific authorization. Three controlled studies examine 500 synthetic requests balanced across categories, 20 ambiguous requests with five separate clear controls, and 61 API access and state-transition cases using MySQL. Recommendations matched provisional reference labels in 449 of 500 cases (89.8\%), with a macro-F1 of 0.8969. A fixed keyword comparator forced a category on six ambiguous cases; the active policy deferred all 20 to review. However, it also deferred every clear control because automatic routing was globally disabled. All 61 selected access and transition cases met their expected outcomes; 37 rejected actions left nine protected business tables unchanged. The routing texts and labels were AI-authored and have not received independent domain review. Consequently, the findings establish provisional category agreement and selected workflow safeguards, rather than verified governmental jurisdiction accuracy. Participant usability results remain pending. The experiments show why classification quality, fallback burden, and access enforcement must be reported separately.
\keywords{Public service workflow \and Request routing \and Human review \and Access isolation \and Prototype evaluation}
\end{abstract}

\section{Introduction}
Public service workflows require requests to reach departments with the appropriate responsibilities and to remain accessible only to authorized users. An online submission channel alone does not establish who should handle a request, how it should be followed up, or which officers may examine its information. Incorrect routing can require reassignment and postpone appropriate follow-up. Unnecessarily broad access can expose information to staff who are not involved in handling the request. These concerns are relevant to accountable digital government and its safeguards~\cite{oecd2025governing}. Routing and authorization therefore require evaluation beyond successful form submission.

This study examines Smart Government Workflow Automation (SGWA), a web prototype serving citizens, departmental staff, and administrators. Its catalog contains 25 prototype service categories, including population administration, health, public works, transportation, and social services. The catalog is an experimental taxonomy, not a verified representation of the current Lamongan organization. A damaged road accompanied by standing water illustrates possible ambiguity between road maintenance and water management. Shared terms alone do not establish jurisdiction; the location, asset ownership, and responsible authority may require clarification. This is a prototype scenario, not an incident established through institutional observation or interviews.

Explicit routing rules encode conditions and destination mappings, whereas supervised text classifiers learn category distinctions from labeled examples~\cite{li2022survey}. SGWA combines these mechanisms: a TF-IDF and logistic regression model recommends one primary category, while routing rules map that recommendation to workflow assignments. These stages must be distinguished. Ambiguous, conflicting, or unsupported assignments require a documented fallback. Human-in-the-loop research supports treating such intervention as part of the process~\cite{wu2022survey}, but its presence alone does not verify that the final decision is correct. Reference labels and evidence about departmental responsibility remain necessary.

The research question is: \emph{Are requests routed to the appropriate departments, and are ambiguous cases handled without exposing information across unauthorized departmental boundaries?} We contribute three reproducible pilot studies separating category recommendation, fallback policy, and access enforcement. The first evaluates 25-category recommendations, the second compares the active policy with a fixed keyword comparator, and the third exercises authorization and terminal-state guards. The single-label outcome concerns one primary category; additional workflow assignments are separate decisions. Model scores and keyword counts are not treated as calibrated probabilities. Because routing labels lack independent domain review and usability testing is pending, the conclusions are restricted to synthetic scenarios and selected implementation cases.

\section{Related Work}
__RELATED__

\section{Research methodology}\label{sec:methodology}
\subsection{Study scope and reference provenance}
The unit of analysis is a request in SGWA's prototype taxonomy. Study~1 evaluates one primary category per text, rather than a set of simultaneously predicted departments. Additional departmental tasks are supported operationally but are not evaluated as multi-label predictions. Study~2 evaluates response actions, including review and clarification, because an ambiguous request need not have one justified destination. Study~3 evaluates server-side authority and state transitions independently of classifier performance.

The 500 Study~1 texts and their proposed labels and reasons were drafted using AI before prediction. Human-review fields remain unapproved. A subsequent review by the same AI author retained all proposed labels; it is neither independent nor blind domain validation. It marked 467 cases as semantically consistent with the prototype taxonomy and 33 as conditional on further jurisdictional or contextual evidence. Forty cases belong to two catalog categories affected by a documented organizational merger, overlapping four of the 33 conditional cases; therefore, 69 unique cases carry at least one caution. No case was excluded or relabeled to improve the reported results.

The official Lamongan website carries an announcement that Regulation No.~6 of 2025 merged the industry/trade and cooperatives/micro-enterprise offices~\cite{lamonganmerger}. This notice supports a concrete taxonomy limitation, not a full legal validation of all 25 categories. Seven official pages were consulted during the AI review, but they do not establish an individually verified authority label for every text. No field interviews or institutional observations were collected. The research problem is therefore framed as a prototype requirement rather than an empirical finding about a government office.

\subsection{Study 1: balanced category recommendation pilot}
The frozen corpus contains 500 newly drafted Indonesian texts, with 20 texts per category. The active classifier had been developed from 2,500 synthetic examples, partitioned into 2,000 training examples and a separate 500-example development holdout. The new pilot corpus was not used for retraining or rule adjustment. Normalized exact-text comparisons found no overlap with the checked local development files. However, the categories and service themes informed text drafting, and semantic or scenario-family independence has not been established. Balanced purposive sampling does not reproduce the distribution of citizen requests.

The active classifier was invoked offline with the frozen texts. The evaluation recorded the top category, all category scores, the active departmental catalog, and the routing policy configuration through a read-only database snapshot. It did not submit 500 requests through the web form or observe 500 administrator decisions. A category recommendation is counted as a match when it equals the provisional reference category. We report a confusion matrix, per-category precision, recall, and F1, macro-F1, and recommendation accuracy. For class $c$,
\begin{equation}
P_c=\frac{TP_c}{TP_c+FP_c},\qquad
R_c=\frac{TP_c}{TP_c+FN_c},\qquad
F1_c=\frac{2P_cR_c}{P_c+R_c},\quad
F1_{\mathrm{macro}}=\frac{1}{25}\sum_{c=1}^{25}F1_c.
\end{equation}
All classes have support 20. Accuracy is the number of matching top categories divided by 500. These quantities measure agreement with the provisional labels, not independently established jurisdiction accuracy.

\subsection{Study 2: ambiguity and keyword comparator}
Twenty additional synthetic scenarios cover four conditions: minimal information, multiple issues, out-of-scope requests, and missing responsibility context, with five cases per condition. Five semantically clear controls are evaluated separately. References specify a preferred action and, where applicable, an acceptable fallback. Ten cases prefer clarification; review is accepted as a coarse safe fallback but is not equivalent to generating a clarification question. The scenarios, references, and comparator were AI-authored and frozen before inference. They have not been independently reviewed.

The fixed comparator contains 125 keywords or phrases, five per category, based on existing prototype service themes. After the recorded text normalization, it counts distinct whole-word or phrase matches. A unique positive maximum produces a simulated single-category routing action; a tie or no match produces review. Counts are integer matching scores, not probabilities. The same 25 texts are evaluated with this comparator and the active ML-assisted policy, without post-result keyword tuning. Outcomes include forced assignments on review cases, acceptable fallback, clear-control handling, and exact preferred-action agreement. We do not force the ambiguous scenarios into a single-label departmental confusion matrix.

\subsection{Study 3: access isolation and terminal-state protection}
The access pilot uses six synthetic identities: two citizens, staff from departments A and B, one unassigned staff member, and an administrator. Departments A and B represent population/civil registration and health. Seven fixture requests cover pending, processing, approved, rejected, shared, and escalated situations. Two synthetic PDF fixtures exercise protected file access. Sixty-one predeclared cases include cross-owner reads, cross-department reads and mutations, query-filter attempts, shared-task authority, unauthenticated access, stale versions, and attempts to reopen terminal requests without an authorized mechanism.

Each action uses FastAPI's in-process TestClient, real authentication handlers and MySQL storage. Expected HTTP results and database effects are specified in the case matrix. Before and after each action, the harness hashes rows and columns in nine protected business tables and checks fixture-file hashes. Authentication preparation occurs before the snapshot so legitimate login activity is not mistaken for a business mutation. Rejected actions must leave these protected data unchanged. Positive controls establish that authorized reads and four legitimate mutations remain possible. Sixty-one cases are exercised inside one automated test function; they are not 61 separate pytest test functions.

\subsection{Reproducibility and pending usability evaluation}
The evidence packages preserve frozen texts and references, baseline keywords, predictions, case matrices, logs, source snapshots, configuration metadata, and SHA-256 manifests. The evaluated working tree includes uncommitted changes; a commit identifier alone is insufficient to reproduce it. Readers should use the saved snapshots and hashes. Study~1 and Study~2 preserve the model artifact and environment identifiers, while Study~3 retains the final run's source and case-level database comparisons.

A separate citizen-interface usability study is planned with eight campus peers as a convenience sample. Tasks concern submitting a request, finding it again, interpreting status and department, and reading the result. Planned measures include independent completion, completion with help, elapsed task time, errors, assistance, and comments. Network or tunnel failures and administrator waiting time must be recorded separately from participant task time. At manuscript preparation, no participant outcomes, usability scores, or observed staff workload are available. None is inferred from screenshots or automated tests.

\section{System design and experimental setup}\label{sec:system}
\subsection{Platform and departmental assignment}
SGWA uses a React/TypeScript frontend, a Python FastAPI backend, SQLAlchemy, MySQL, and a background SLA worker. Citizens submit descriptions and inspect progress. Administrators review recommendations and assign departments. Staff act on tasks assigned to their own department. Supporting files, result records, notifications, and request history connect these stages. The primary recommendation is single-label; optional supporting departments are explicit workflow assignments.

\begin{figure}[t]
\centering
\fbox{\parbox{0.92\linewidth}{\centering
Citizen request $\longrightarrow$ text classifier $\longrightarrow$ category recommendation\\[3pt]
Routing rules and policy $\longrightarrow$ administrator review/assignment\\[3pt]
Authorized departmental task $\longrightarrow$ decision and citizen-visible history\\[3pt]
FastAPI authorization and state guards $\longleftrightarrow$ MySQL records}}
\caption{SGWA's evaluated separation of recommendation, assignment, workflow, and storage. Review is mandatory under the active policy.}
\label{fig:architecture}
\end{figure}

\subsection{Classification, rules, and human fallback}
The frozen model identifier is \texttt{ml25-4bb961bc5928e05b937a1be5}. Its TF-IDF/logistic regression recommendations feed departmental mapping, rather than directly granting a department access. At evaluation, category-to-active-department identity mapping was available and there were no additional configured routing-rule rows. The configured score threshold was 0.70, but automatic routing was globally disabled. Consequently, threshold exceedance alone could not create an automatic assignment. This policy setting is central to interpreting both routing studies.

An administrator's \emph{assign/forward} action creates departmental work; a direct final approval can complete a request without creating a new assignment. A saved classifier correction is a separate record for possible future training and does not itself reroute an existing request. These distinctions prevent interpreting an informational recommendation or feedback record as a completed operational assignment. Citizen and departmental views omit detailed ML diagnostics; administrators can inspect them. The prototype screenshots document an example flow, whereas the experiments below provide separate quantitative evidence.

\subsection{Authorization and execution conditions}
Request ownership governs citizen access; departmental task assignment governs staff access; administrators have review authority. For a shared request, both assigned departments may read it, but a staff member may mutate only their own departmental task. Terminal-state and version guards are enforced on the server, including direct endpoint calls. This implements object-specific checks relevant to the authorization risk discussed by OWASP~\cite{owasp2023bola}.

\begin{table}[t]
\caption{Experimental material and execution conditions. All data are synthetic.}
\label{tab:conditions}\centering\small
\begin{tabular}{p{0.13\linewidth}p{0.37\linewidth}p{0.39\linewidth}}
\toprule
Study & Material & Execution and scope\\\midrule
1 & 500 texts; 25 categories; 20 per category & Offline model inference and read-only catalog/policy snapshot; Python 3.12.15, scikit-learn 1.9.1.\\
2 & 20 ambiguity scenarios plus 5 clear controls; 125 comparator terms & Paired offline policy simulation; same active model and configuration as Study~1.\\
3 & 61 API cases; 6 identities; 7 requests; 2 file fixtures & TestClient with MySQL 8.4.11 in isolated test database, port 3308; schema created from ORM models.\\
\bottomrule
\end{tabular}
\end{table}

Study~3 does not test migration scripts or equivalence to the deployed Docker image. It exercises server handlers in process, rather than browser behavior, external network transport, TLS, or load. ML inference is explicitly excluded from that test. The isolated test database is separate from the demonstration database.

\section{Results and discussion}\label{sec:results}
\subsection{Study 1: category agreement and error distribution}
The model's top recommendation matched 449 of 500 provisional labels (89.8\%); 51 cases disagreed. Macro-F1 was 0.8969. Table~\ref{tab:perclass} gives precision, recall, F1, and support for every category; English names are descriptive translations of the frozen Indonesian catalog. Figure~\ref{fig:f1} visualizes the variation, while Appendix~\ref{sec:cm} presents the full confusion matrix. These results concern recommendations. The active routing policy sent all 500 cases to review: automatic coverage was 0\%, and accuracy among automatic assignments is undefined because no such assignment occurred.

\begingroup\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{longtable}{r p{0.46\linewidth} r r r r}
\caption{Study 1: provisional per-category results. P, R, and F1 are percentages; all reference labels remain unvalidated by human domain reviewers.}\label{tab:perclass}\\
\toprule ID & Prototype category & $n$ & P & R & F1\\\midrule
\endfirsthead
\multicolumn{6}{l}{\tablename\ \thetable\ (continued)}\\
\toprule ID & Prototype category & $n$ & P & R & F1\\\midrule
\endhead
__PERCLASS__
\midrule\multicolumn{3}{l}{Macro-F1} & \multicolumn{3}{r}{89.69}\\
\bottomrule
\end{longtable}
\endgroup

\begin{figure}[p]
\centering
\begin{tikzpicture}
\begin{axis}[width=\linewidth,height=6cm,ymin=0,ymax=105,
xmin=0.3,xmax=25.7,xtick={1,...,25},xticklabel style={font=\tiny},
ytick={0,20,40,60,80,100},xlabel={Category ID (Table~\ref{tab:perclass})},
ylabel={F1 (\%)},ymajorgrids=true,grid style={gray!20},bar width=3pt]
\addplot[ybar,fill=teal!65,draw=teal!80!black] coordinates {__F1COORDS__};
\end{axis}
\end{tikzpicture}
\caption{F1 against provisional AI-authored labels for 25 categories, with 20 texts per category. The differences are descriptive pilot results.}
\label{fig:f1}
\end{figure}

Archives/libraries had the lowest F1 (73.2\%), followed by transportation (76.5\%). Transportation recall was 65.0\%, while water-resources recall was 70.0\%. Three water-resources references were predicted as housing/settlements/public facilities, and three tourism/culture references were predicted as archives/libraries. Two population/civil-registration references were predicted as communication/informatics. These patterns suggest overlap between service vocabulary and topic categories; they do not establish causal feature attribution or legal misrouting.

For example, an official parking-tariff sign can emphasize information provision even when the provisional task concerns transportation. Digital identity can similarly overlap with information technology vocabulary. Such cases indicate that category names and shared terms are insufficient substitutes for responsibility context. Table~\ref{tab:failures} connects representative disagreements to this interpretation. The pilot corpus differs from the model's earlier development holdout, so its higher score must not be described as improvement caused by training or a code change.

\subsection{Study 2: ambiguity, comparator, and review burden}
On the 20 ambiguous cases, the keyword comparator forced a single category in six cases and used an acceptable fallback in 14. The active policy forced none and deferred all 20. However, it also deferred all five clear controls, whereas the comparator assigned each control to its provisional category. Table~\ref{tab:ambiguity} reports the condition-level counts, and Fig.~\ref{fig:ambiguity} shows the resulting tradeoff. The final policy's caution follows from globally disabled automatic routing; it is not evidence of a learned semantic ambiguity detector or general superiority to rule-based routing.

\begin{table}[t]
\caption{Study 2: paired outcomes. B = keyword baseline; F = active final policy. A forced route is an assignment on a case whose reference requires review or clarification.}
\label{tab:ambiguity}\centering\small
\begin{tabular}{p{0.38\linewidth}r rr rr}
\toprule & & \multicolumn{2}{c}{Forced routes} & \multicolumn{2}{c}{Review}\\
Condition & $n$ & B & F & B & F\\\midrule
Minimal information &5&0&0&5&5\\
Multiple issues &5&4&0&1&5\\
Out of scope &5&1&0&4&5\\
Missing responsibility context &5&1&0&4&5\\\midrule
Ambiguous subtotal &20&6&0&14&20\\
Clear controls &5&0&0&0&5\\\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\begin{tikzpicture}
\begin{axis}[ybar,bar width=12pt,width=\linewidth,height=5.8cm,
ymin=0,ymax=23,ytick={0,5,10,15,20},ylabel={Number of cases},
symbolic x coords={Forced on ambiguous,Review on ambiguous,Review on clear},
xtick=data,xticklabel style={font=\scriptsize,text width=2.7cm,align=center},
enlarge x limits=0.23,legend style={at={(0.5,1.02)},anchor=south,legend columns=2,font=\small},
ymajorgrids=true,grid style={gray!20}]
\addplot[fill=gray!50] coordinates {(Forced on ambiguous,6) (Review on ambiguous,14) (Review on clear,0)};
\addplot[fill=teal!65] coordinates {(Forced on ambiguous,0) (Review on ambiguous,20) (Review on clear,5)};
\legend{Keyword comparator,Active policy}
\end{axis}
\end{tikzpicture}
\caption{Study 2: avoiding forced assignments increases the potential review queue under the current mandatory-review policy. Ambiguous and clear groups have denominators 20 and 5, respectively.}
\label{fig:ambiguity}
\end{figure}

Neither method generated an automated clarification response. Both matched the exact preferred action in 10 of 25 cases. This is consistent with accepting review as a coarse fallback for clarification-preferred cases while counting it separately from exact action agreement. Across all 25 inputs, review counts were 14 for the comparator and 25 for the active policy. These counts indicate potential queue volume, not observed correction counts, processing time, or staff effort. The five clear-control category recommendations themselves matched the provisional labels, but two scored below 0.70 and none could bypass the global policy. Clear-control fallback therefore cannot automatically be labeled operationally unnecessary.

Four of the six comparator failures involved multiple issues. For example, a KTP and business-licensing request contained more licensing phrases than population-administration phrases and received one licensing destination despite requiring review. An out-of-scope national-road report matched road-maintenance terms without establishing county responsibility. A parking report lacking public/private asset context likewise received a transportation destination. These failures illustrate the limits of a unique keyword maximum when responsibility depends on context outside the matched terms.

\subsection{Study 3: authorization and terminal-state outcomes}
All 61 selected cases met their expected outcomes (Table~\ref{tab:access}). Of these, 37 were rejected actions and 24 were allowed controls. The 37 rejected actions preserved every checked protected business table, giving 333 table comparisons (37 actions times nine tables), with fixture-file integrity checks also unchanged. Across all cases, the package contains 549 table-level before/after records. The nine tables cover requests, workflows, events, classification results, result documents, attachments, mock checks, notifications, and audit logs.

\begin{table}[t]
\caption{Study 3: selected API cases. The first four rows are denied cases; the last contains authorized positive controls.}
\label{tab:access}\centering\small
\begin{tabular}{p{0.60\linewidth}rr}
\toprule Case group & Cases & Expected outcomes met\\\midrule
Ownership and departmental authority &22&22\\
Terminal-state protection &13&13\\
Stale-version rejection &1&1\\
Unauthenticated request &1&1\\
Authorized positive controls &24&24\\\midrule
Total &61&61\\\bottomrule
\end{tabular}
\end{table}

The observed HTTP distribution was one 401, nine 403, thirteen 404, fourteen 409, and twenty-four 200 responses. A concealed unauthorized object can appropriately yield 404, so correctness was judged against the case-specific expectation rather than requiring one universal denial code. Staff A could not read or mutate an unrelated department B request. For a legitimately shared request, both departments could read it, while staff A could not change department B's task. Positive controls included valid processing, approval, and administrator assignment; thus, denial outcomes were not merely caused by a universally inaccessible API.

Thirteen cases tested terminal guards, including attempts to return approved or rejected requests to active processing and to bypass closure through review or routing endpoints. They were rejected as expected and left the protected records unchanged. The stale-version case was distinct from terminal closure: an ongoing request rejected an outdated version, while an authorized action with the current version succeeded. These findings support the selected server-side boundaries under the fixture conditions. They do not prove isolation for every endpoint, concurrent action, deployment configuration, or side channel.

\begin{table}[t]
\caption{Representative pilot failures and limitations. Study 1 references are provisional; the explanations are interpretive, not verified legal determinations or causal feature analyses.}
\label{tab:failures}\centering\scriptsize
\begin{tabular}{p{0.16\linewidth}p{0.35\linewidth}p{0.39\linewidth}}
\toprule Case & Observed outcome & Interpretation and follow-up\\\midrule
R25-381 & Official parking-tariff sign: transportation reference; communication/informatics prediction & Information vocabulary overlaps with the service topic; clarify the responsible parking asset.\\
R25-452 & Digital identity status: population/civil-registration reference; communication/informatics prediction & Digital terminology does not itself determine administrative responsibility.\\
A2-07 & KTP plus business licensing: comparator chose licensing & More matches for one issue hide the need to resolve multiple responsibilities.\\
A2-15 & National-road report: comparator chose prototype road category & Lexical match does not establish asset ownership or county jurisdiction.\\
All clear controls & Active policy used review for all five & Global automatic-routing disablement limits coverage; measure actual review effort before operational claims.\\
\bottomrule
\end{tabular}
\end{table}

\subsection{Relationship to the research question and threats to validity}
The studies answer different parts of the research question. Study~1 quantifies provisional category agreement, not final officer assignment. Study~2 demonstrates the active policy's conservative response and its review-volume tradeoff. Study~3 supports selected authorization and closure invariants after assignments exist. Combining them does not establish that every correctly classified request is processed correctly or that ambiguous requests receive correct human decisions.

The principal validity threat is reference quality. The text author, label proposer, comparator author, and post-hoc AI reviewer are not independent. No human domain reviewer has validated the 500 category labels or 25 action references. Shared service themes, explicit context, balanced categories, and synthetic language can inflate apparent agreement relative to real citizen inputs. Exact deduplication does not establish semantic independence. The 69 cautioned Study~1 cases and the merger notice further limit claims that the prototype categories equal current institutional authority. No statistical population generalization is made.

Study~2 compares one fixed keyword heuristic with one active mandatory-review configuration; it does not compare all rule systems or isolate the classifier's causal benefit. Study~3 covers two departments and selected resources using ORM-created fixtures and in-process HTTP. It excludes deployment equivalence, browser usability, concurrency, load, TLS, and a full security audit. Prototype screenshots provide product evidence but cannot substitute for quantitative user observations. Eight planned campus participants would constitute a convenience sample and would not by themselves represent citizens or civil servants generally. No reduction in real service duration or improvement in real institutional service quality is claimed.

\section{Conclusion and future work}
Within SGWA's synthetic 25-category pilot, 449 of 500 recommendations agreed with provisional reference labels (89.8\%), with macro-F1 0.8969. On 20 ambiguous scenarios, a fixed keyword comparator forced six assignments, while the active policy deferred all cases; it also deferred all five clear controls because automatic routing was disabled. Thus, conservative handling currently trades automatic coverage for potential review volume. In the separate API pilot, all 61 selected access and transition cases met expectations, and all 37 rejected actions preserved the nine protected business tables.

The research question is therefore only partially answered: the experiments support provisional category agreement, a conservative fallback configuration, and selected access safeguards, but do not establish correct governmental jurisdiction or correct human resolution of ambiguous requests. Independent domain review, an updated institution-to-category mapping, and semantically independent real-world texts are required before stronger routing claims. The next empirical step is the planned citizen usability study, reported using actual task observations rather than inferred scores. Future work should measure review effort, examine additional authorization resources and concurrency, and evaluate alternative routing policies without tuning on the frozen pilot texts. Service-duration benefits remain an open question requiring appropriate field evidence.

\appendix
\section{Full category confusion matrix}\label{sec:cm}
\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{axis}[width=\linewidth,height=\linewidth,
xmin=0.5,xmax=25.5,ymin=0.5,ymax=25.5,y dir=reverse,
xtick={1,...,25},ytick={1,...,25},tick label style={font=\tiny},
xlabel={Predicted category ID},ylabel={Provisional reference category ID},
colormap={paperblue}{color(0)=(white);color(1)=(teal!85!black)},
point meta min=0,point meta max=20,colorbar,
colorbar style={ylabel={Number of texts},ytick={0,5,10,15,20},font=\scriptsize}]
\addplot[scatter,only marks,scatter src=explicit,mark=square*,mark size=2.9pt]
coordinates {__CMCOORDS__};
\end{axis}
\end{tikzpicture}
\caption{Study 1 confusion matrix: each row contains 20 texts; category IDs follow Table~\ref{tab:perclass}. Cell counts, including zeros, are available in the accompanying CSV. Labels are AI-authored and provisional.}
\label{fig:confusion}
\end{figure}

\begin{thebibliography}{9}
__BIB__
\bibitem{lamonganmerger}
Dinas Perindustrian dan Perdagangan Kabupaten Lamongan:
Organizational-change announcement referring to Regulation No.~6 of 2025.
Notice displayed on the UTTP service page (underlying service article dated 7 September 2022).
\url{https://disperindag.lamongankab.go.id/posting/6243}.
Accessed 25 October 2026.
\end{thebibliography}
\end{document}
'''
tex = tex.replace('__RELATED__', related.strip()).replace('__PERCLASS__', table_rows)
tex = tex.replace('__F1COORDS__', f1coords).replace('__CMCOORDS__', cmcoords).replace('__BIB__', bib.strip())
from add_paper_screenshots import update_tex
tex = update_tex(tex)
(OUT / 'main.tex').write_text(tex, encoding='utf-8')
print(f'Prepared {len(tex)} characters; {len(rows)} category rows; {len(cmcoords.splitlines())} matrix cells.')
