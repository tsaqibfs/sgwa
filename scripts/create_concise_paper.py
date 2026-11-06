"""Generate a separate, compact LLNCS manuscript from the recorded pilot results."""
from pathlib import Path
import csv
import re

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'paper-routing-study/main.tex').read_text(encoding='utf-8-sig')
bib=src.split(r'\begin{thebibliography}{15}',1)[1].split(r'\end{thebibliography}',1)[0].strip()
classes=list(csv.DictReader((ROOT/'outputs/routing-evaluation-20261025-provisional/per_class.csv').open(encoding='utf-8-sig')))
names=['Disaster management','Civil registration','Archives and libraries','Health','Communication and IT','Cooperatives and microbusiness','Environment','Food and agriculture','Tourism and culture','Village empowerment','Women and child protection','Youth and sports','Education','Population control and family','Transportation','Fisheries','Industry and trade','Integrated licensing','Housing and settlements','Livestock and animal health','Public works: roads','Public works: water','Public order','Social services','Manpower']
rows=[]
for i,r in enumerate(classes):
    rows.append(f"{i+1} & {names[i]} & {100*float(r['precision']):.1f} & {100*float(r['recall']):.1f} & {100*float(r['f1-score']):.1f} \\\\")
matrix=list(csv.reader((ROOT/'outputs/routing-evaluation-20261025-provisional/confusion_matrix.csv').open(encoding='utf-8-sig')))
coords=' '.join(f'({j},{i}) [{n}]' for i,row in enumerate(matrix[1:],1) for j,n in enumerate(row[1:],1))
tex=r'''\documentclass[runningheads]{llncs}
\usepackage[T1]{fontenc}
\usepackage{newtxtext}
\usepackage[varvw]{newtxmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage[section]{placeins}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{arrows.meta,positioning}
\usepackage[hidelinks]{hyperref}
\setlength{\emergencystretch}{1em}
\begin{document}
\raggedbottom
\title{Evaluating Rule-Based Request Routing and Departmental Access Isolation in a Public Service Workflow}
\titlerunning{Request routing and departmental access isolation}
\author{Tsaqib Fadhlurrahman Soka \and Muhammad Firman Saputra}
\authorrunning{T. F. Soka and M. F. Saputra}
\institute{Electronic Engineering Polytechnic Institute of Surabaya, Surabaya, Indonesia\\
\email{tsaqibsoka@it.student.pens.ac.id}\\\email{mfirman@it.student.pens.ac.id}}
\maketitle
\begin{abstract}
Public service requests require suitable departmental destinations and access restrictions. This study evaluates Smart Government Workflow Automation (SGWA), a web prototype combining text classification, category-to-department mapping, administrator review and request-specific authorization. An offline pilot used 500 AI-authored texts, equally distributed across 25 prototype categories; 449 recommendations matched provisional labels (89.8\%, macro-F1 0.8969). On 20 ambiguous scenarios and five clear controls, a fixed keyword comparator forced six ambiguous assignments, while the active policy deferred all 25 cases because automatic routing was disabled. In an isolated MySQL/API test, 61 selected authorization and state-transition cases met expected outcomes; 37 rejected actions left nine protected tables unchanged. Five campus participants were recorded as completing a session independently; three reported that registration passwords could not be displayed, and one reported an incorrect category for a wet family-card request. The mean reported duration was 2:28 minutes, subject to clarification of timing boundaries. Synthetic references lack independent domain validation, and usability observations are a small convenience sample. Results therefore demonstrate provisional category agreement and selected safeguards, not verified jurisdiction accuracy or reduced service time.
\keywords{Public services \and Request routing \and Human review \and Access isolation \and Usability}
\end{abstract}

\section{Introduction}
Public service requests often span departmental responsibilities. A wrong destination can delay follow-up and require reassignment, while overly broad access may expose a citizen's information to unrelated officers. Online submission alone does not demonstrate correct routing or authorization. Digital government therefore requires transparent decisions and safeguards~\cite{oecd2025governing}.

Smart Government Workflow Automation (SGWA) is a web prototype for citizens, administrators and departmental staff, using 25 prototype service categories. A damaged road with standing water illustrates a potentially ambiguous choice between road and water management; ownership and jurisdiction may require clarification. This is a prototype scenario rather than an institutionally observed incident. The 25 categories do not claim to reproduce Lamongan's current organization: an official notice reports a merger affecting two catalog categories~\cite{lamonganmerger}.

Rule-based mappings offer inspectable destination conditions; supervised classifiers learn category distinctions from labeled texts~\cite{li2022survey}. SGWA uses TF-IDF/logistic regression to recommend a primary category, maps categories to departments and retains administrator review. Conflicts and unsupported requests require human fallback, whose effectiveness must itself be evaluated~\cite{wu2022survey,vaccaro2024combination}. A score is a decision aid, not a calibrated probability of correctness~\cite{silva2023calibration}.

We ask: \emph{Are requests routed to the appropriate departments, and are ambiguous cases handled without exposing information across unauthorized departmental boundaries?} We evaluate provisional category agreement, a keyword comparator versus the active fallback policy, and server-side access/state guards. The initial classifier outcome is single-label; additional departmental workflow tasks do not constitute multi-label prediction. A separate five-person usability observation supplies initial interface feedback.

\section{Related work}
Table~\ref{tab:related} contrasts representative foundations. Madyatmadja et al.~\cite{madyatmadja2023complaints} compare supervised classifiers for LAKSA complaints with officer-annotated categories, highlighting the need for domain-reviewed labels. Majumder et al.~\cite{majumder2025tipline} separate irrelevant EPA tips from division routing; their scope and LLM method differ from SGWA. WRENCH~\cite{zhang2021wrench} studies noisy and abstaining labeling functions, not government workflow authorization. Ariyana et al.~\cite{ariyana2025multilabel} evaluate multi-label complaints, whereas our pilot scores one primary category.

\begin{table}[!htbp]\centering\footnotesize
\caption{Related work and its relevance to the prototype.}\label{tab:related}
\begin{tabular}{p{0.20\linewidth}p{0.31\linewidth}p{0.37\linewidth}}\toprule
Study & Data/approach & Basis and limitation for SGWA\\\midrule
LAKSA~\cite{madyatmadja2023complaints} & Officer-annotated complaint categories; supervised models & Domain labels and class-level analysis; SGWA labels lack expert review.\\
EPA tips~\cite{majumder2025tipline} & Relevance screening and LLM routing & Out-of-scope handling; different agency, task and model.\\
WRENCH~\cite{zhang2021wrench} & Noisy, overlapping/abstaining heuristic labels & Documents rule limits; not an authorization study.\\
Wargaku~\cite{ariyana2025multilabel} & Multi-label complaint classification & Defines the multi-label alternative to our single primary output.\\
Human/AI~\cite{wu2022survey,vaccaro2024combination} & Surveys and human--AI experiments & Motivates evaluating reviewer actions; a queue alone proves no benefit.\\
\bottomrule\end{tabular}\end{table}

Synthetic-text studies support transparent reporting of generation and evaluation but do not validate governmental authority~\cite{he2022generate,li2023synthetic,ramesh2025synthtexteval}. Data leakage can invalidate performance estimates~\cite{kapoor2023leakage}. For access, OWASP identifies missing object-specific checks as a risk when APIs accept record identifiers~\cite{owasp2023bola}. SGWA jointly examines these concerns; it does not claim earlier systems lacked access controls.

\section{System design and methodology}\label{sec:methods}
\subsection{Prototype and decision flow}
SGWA comprises a React/TypeScript client, Python FastAPI and SQLAlchemy services, MySQL, and an SLA worker (Fig.~\ref{fig:architecture}). Citizens submit text and inspect status; administrators review and assign departments; authorized staff process assigned tasks. The model recommendation does not grant access. Each API operation checks ownership or task assignment and applicable status/version guards. A direct administrator approval can close a request; forwarding creates a departmental task. A saved classification correction is a separate record and does not itself reroute a request.

\begin{figure}[!htbp]\centering
\begin{tikzpicture}[node distance=3mm,
box/.style={draw,rounded corners=1pt,align=center,text width=8.9cm,font=\small,inner sep=3pt},
arr/.style={-{Latex[length=1.6mm]},thick}]
\node[box] (ui) {React/TypeScript: citizen $\mid$ administrator $\mid$ departmental staff};
\node[box,below=of ui] (api) {FastAPI: authentication, request-specific authorization, state guards};
\node[box,below=of api] (logic) {TF-IDF/logistic regression $\to$ category mapping $\to$ administrator review $\to$ staff task};
\node[box,below=of logic] (db) {SQLAlchemy/MySQL: requests, tasks, history, files and notifications; SLA worker};
\draw[arr] (ui)--(api);\draw[arr] (api)--(logic);\draw[arr] (logic)--(db);
\end{tikzpicture}
\caption{Prototype architecture and decision flow. Review was mandatory in the evaluated configuration.}\label{fig:architecture}\end{figure}

The classifier joins title and description, applies NFKC, lowercasing, whitespace normalization and a limited Indonesian alias dictionary, then uses word unigram/bigram TF-IDF with sublinear term frequency and logistic regression ($C=4$, maximum 1,000 iterations, seed 42). This is not a general typo corrector. The active model was \texttt{ml25-4bb961bc5928e05b937a1be5}; threshold 0.70 was configured but automatic routing was globally disabled. Category identity mapping was active with no additional configured routing-rule rows.

\subsection{Experimental design}
\textbf{Study 1.} An AI-authored, frozen corpus contains 500 new texts and proposed reference categories, 20 per category. Training used 2,000 examples and an earlier separate 500-example development holdout. Exact normalized text checks found no overlap with checked development files; shared themes and semantic overlap remain possible. The same AI author conducted a later non-blind review; no independent human/domain validation occurred. Offline inference recorded top categories, class scores and policy/catalog information without submitting 500 browser requests. We calculate accuracy, class precision/recall/F1 and macro-F1 from the provisional single-label references.

\textbf{Study 2.} Twenty AI-authored scenarios cover minimal information, multiple issues, out-of-scope and missing responsibility context (five each), plus five clear controls. Both methods used the same frozen cases. The baseline counts matches from 125 fixed category phrases, routes a unique positive maximum and otherwise defers to review; the active policy uses the recorded model/policy. A review is accepted as a coarse fallback on clarification-preferred cases, but is not an automatically generated clarification. We count forced assignments, fallback and control handling without a single-label confusion matrix for ambiguous cases.

\textbf{Study 3.} Sixty-one predeclared API cases use six synthetic identities, two departments, seven requests and two fake PDF fixtures. FastAPI TestClient runs in process with real authorization handlers and isolated MySQL 8.4.11 storage. We compare expected/actual HTTP status and pre/post hashes of nine protected business tables and files. The test does not exercise a browser, deployed-image equivalence, migration, concurrency, TLS or load.

\textbf{Usability.} Five campus participants form a convenience sample. The available records contain an overall independent outcome, one duration and optional comment per person. Timing is interpreted as minutes:seconds; exact task sequence, timer boundaries, device/network conditions and consent documentation require confirmation. There are no supplied task-level error counts or SUS scores. The screenshots in Fig.~\ref{fig:prototype} document a synthetic demonstration, not the usability sessions.

\begin{figure}[!htbp]\centering
\begin{minipage}{.48\linewidth}\centering\includegraphics[width=\linewidth]{images/prototype-01-citizen-form.png}\\{\footnotesize (a) Citizen submits request}\end{minipage}\hfill
\begin{minipage}{.48\linewidth}\centering\includegraphics[width=\linewidth]{images/prototype-03-admin-assignment.png}\\{\footnotesize (b) Administrator selects destination}\end{minipage}\\[3pt]
\begin{minipage}{.48\linewidth}\centering\includegraphics[width=\linewidth]{images/prototype-04-department-processing.png}\\{\footnotesize (c) Department processes task}\end{minipage}\hfill
\begin{minipage}{.48\linewidth}\centering\includegraphics[width=\linewidth]{images/prototype-05-citizen-result.png}\\{\footnotesize (d) Citizen sees final history}\end{minipage}
\caption{Prototype screens from a simulated lost-KTP information request. The administrator image shows selection before forwarding; subsequent staff and citizen screens show the demonstrated workflow. These images do not prove issuance of an identity document or unauthorized-access denial.}\label{fig:prototype}\end{figure}

\section{Results and discussion}\label{sec:results}
\subsection{Study 1: recommendation agreement}
The top recommendation agreed with 449/500 provisional labels (89.8\%); macro-F1 was 0.8969. Table~\ref{tab:class} lists every class, and Fig.~\ref{fig:cm} shows reference versus predicted categories. All 500 inputs were deferred to manual review, giving zero automatic coverage; automatic-assignment accuracy is undefined. These are recommendation results, not 449 completed departmental assignments.

\begin{table}[!htbp]\centering\footnotesize\setlength{\tabcolsep}{4pt}
\caption{Per-category precision (P), recall (R), and F1 (percent); $n=20$ for every class. Labels are provisional.}\label{tab:class}
\begin{tabular}{r p{.48\linewidth} r r r}\toprule ID & Prototype category & P & R & F1\\\midrule
__CLASS_ROWS__
\midrule\multicolumn{4}{l}{Macro-F1} & 89.69\\\bottomrule\end{tabular}\end{table}

\begin{figure}[!htbp]\centering
\begin{tikzpicture}\begin{axis}[width=7.8cm,height=7.8cm,xmin=.5,xmax=25.5,ymin=.5,ymax=25.5,y dir=reverse,xtick={5,10,15,20,25},ytick={5,10,15,20,25},tick label style={font=\scriptsize},xlabel={Predicted category ID},ylabel={Provisional reference ID},colormap={paperblue}{color(0)=(white);color(1)=(teal!85!black)},point meta min=0,point meta max=20,colorbar,colorbar style={ylabel={Count},font=\scriptsize}]
\addplot[scatter,only marks,scatter src=explicit,mark=square*,mark size=2.2pt] coordinates {__MATRIX__};
\end{axis}\end{tikzpicture}
\caption{Provisional confusion matrix; category IDs follow Table~\ref{tab:class}. Each reference row contains 20 cases.}\label{fig:cm}\end{figure}

Archives/libraries had the lowest F1 (73.2\%) and transportation recall was 65\%. Three water-resource references were predicted as housing and three tourism/culture references as archives. Shared vocabulary may contribute, but the evidence does not establish causal feature attribution or legal misrouting. Because the pilot differs from the earlier holdout, scores cannot support a claim of improvement across versions.

\subsection{Study 2: ambiguity and comparison}
The baseline forced six of 20 ambiguous cases into one category and used an acceptable fallback for 14; the active policy deferred all 20. It also deferred all five clear controls, which the baseline routed to their provisional categories (Table~\ref{tab:ambiguity}). Review on clear cases describes potential queue volume, not measured staff workload or necessarily unnecessary review. Neither method generated an automated clarification, and each matched the exact preferred action on 10 of 25 inputs. Mandatory review, rather than demonstrated semantic ambiguity detection, explains the conservative active-policy outcome.

\begin{table}[!htbp]\centering\footnotesize
\caption{Study 2 outcomes on identical synthetic inputs.}\label{tab:ambiguity}
\begin{tabular}{p{.44\linewidth}rrr}\toprule Condition ($n$) & Baseline forced & Baseline review & Policy review\\\midrule
Minimal information (5)&0&5&5\\ Multiple issues (5)&4&1&5\\ Out of scope (5)&1&4&5\\ Missing context (5)&1&4&5\\ Clear controls (5)&0&0&5\\\bottomrule\end{tabular}\end{table}

A combined KTP/licensing request was forced to licensing by the baseline, while a national-road report matched local road-maintenance wording without establishing ownership. These examples illustrate how keyword counts may overlook issue multiplicity and jurisdiction context. The baseline and reference responses were AI-authored and not independently reviewed.

\subsection{Study 3: access and terminal-state cases}
All 61 selected cases met their expectations: 22 authority restrictions, 13 terminal-state guards, one stale-version rejection, one unauthenticated request and 24 authorized controls. Of 37 rejected actions, all retained the nine protected tables (333 before/after table comparisons); the complete run contains 549 table comparisons. Table~\ref{tab:access} gives representative cases. A concealed object can return 404, so outcomes are compared against case-specific expectations. Assigned departments could read a shared request, but staff could not alter another department's task. These are selected in-process tests, not a complete security audit.

\begin{table}[!htbp]\centering\footnotesize\setlength{\tabcolsep}{3pt}
\caption{Selected API cases; paths omit the common \texttt{/api/v1} prefix and IDs refer to fixtures.}\label{tab:access}
\begin{tabular}{p{.11\linewidth}p{.33\linewidth}p{.27\linewidth}p{.16\linewidth}}\toprule ID/role & Endpoint and action & Expected/actual & Protected data\\\midrule
D02/staff A & GET \path{/requests/2}, read B & 404 / 404 & unchanged\\
D07/staff A & PATCH \path{/requests/2/status} & 404 / 404 & unchanged\\
T32/staff A & PATCH \path{/requests/3/tasks/3}, reopen & 409 / 409 & unchanged\\
V01/staff A & PATCH \path{/requests/1/tasks/1}, stale & 409 / 409 & unchanged\\
M01/staff A & PATCH \path{/requests/1/tasks/1}, start & 200 / 200 & five tables changed\\
M02/staff A & PATCH \path{/requests/1/tasks/1}, approve & 200 / 200 & six tables changed\\
\bottomrule\end{tabular}\end{table}

\subsection{Exploratory usability and limitations}
All five participants were recorded as independent. Their reported durations were 2:59, 1:59, 2:49, 2:29 and 2:04, interpreted as minutes:seconds; mean 2:28 and median 2:29. Timer boundaries and tasks require clarification, so these are not validated task-level or service-time measures. Three participants noted that they could not reveal the registration password. One also reported that ``KK basah'' (a wet family card) was categorized as housing instead of civil registration. The full input, model version, score and final assignment were not supplied, so this is a participant-reported error rather than a reproduced inference or proven data disclosure. No comment was recorded for two participants; this does not prove absence of difficulty. No SUS score or error rate can be calculated from the available records.

\begin{table}[!htbp]\centering\footnotesize
\caption{Anonymized participant records; dash means no comment recorded.}\label{tab:usability}
\begin{tabular}{l l l p{.50\linewidth}}\toprule Participant & Outcome & Time & Comment\\\midrule
P1 & Independent & 2:59 & Password visibility during registration.\\
P2 & Independent & 1:59 & --\\
P3 & Independent & 2:49 & Password visibility during registration.\\
P4 & Independent & 2:29 & --\\
P5 & Independent & 2:04 & Password visibility; reported ``KK basah'' category error.\\
\bottomrule\end{tabular}\end{table}

The corpus author, reference proposer, keyword-comparator author and later AI reviewer were not independent. Of 500 references, 33 were marked conditional; 40 belonged to categories affected by an organizational merger, with four overlapping (69 unique cautions). These cautions did not lead to exclusions or relabeling. The synthetic balanced sample, missing domain review and shared themes limit generalization. Study 2 examines one comparator and a mandatory-review configuration, while Study 3 covers selected endpoints and two departments. The campus convenience sample cannot represent all citizens or public officers. Further domain review, independent cases and observed staff corrections are necessary.

\section{Conclusion}
The 25-class synthetic pilot produced 449/500 provisional recommendation matches and macro-F1 0.8969. Mandatory review prevented forced routing in the 20 ambiguity cases but also deferred all five clear controls; it demonstrates a cautious policy and potential review burden, not an ambiguity detector. All 61 selected API cases met expected outcomes and all 37 rejected actions preserved the checked business tables. Five participant sessions were recorded as independent, with three password-visibility comments and one reported KK category error. Thus the question is only partially answered: domain-valid jurisdiction accuracy, actual human correction workload and broader access coverage remain open. Real-world validation and documented usability protocols are required before claiming improved service outcomes.

\FloatBarrier
\begin{thebibliography}{15}
__BIB__
\end{thebibliography}
\end{document}
'''
tex=tex.replace('__CLASS_ROWS__','\n'.join(rows)).replace('__MATRIX__',coords).replace('__BIB__',bib)
out=ROOT/'.superpowers/paper-preparation/concise-main.tex'
out.write_text(tex,encoding='utf-8')
print('Prepared',len(tex),'characters,',len(re.findall(r'\\bibitem\{',tex)),'references,',len(rows),'class rows')
