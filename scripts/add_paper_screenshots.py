"""Attach the supplied prototype screenshots, unchanged, to the LLNCS paper."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'paper-routing-study'
SOURCE = Path('C:/Users/Lenovo/OneDrive/Pictures/Screenshots')
SHOTS = [
    ('Screenshot 2026-10-25 061047.png', 'prototype-01-citizen-form.png'),
    ('Screenshot 2026-10-25 065843.png', 'prototype-02-submitted-request.png'),
    ('Screenshot 2026-10-25 070000.png', 'prototype-03-admin-assignment.png'),
    ('Screenshot 2026-10-25 070130.png', 'prototype-04-department-processing.png'),
    ('Screenshot 2026-10-25 070232.png', 'prototype-05-citizen-result.png'),
]

FRAGMENT = r'''\subsection{Prototype demonstration and screenshot evidence}\label{sec:prototype}
Figures~\ref{fig:citizen-form}--\ref{fig:citizen-result} document a demonstration involving a synthetic request for information about replacing a lost Indonesian identity card (KTP). The sequence covers citizen submission, an initial review state, administrator selection of the population and civil registration department, departmental processing, and the citizen-visible final history. The screenshots were supplied from the prototype on 25 October 2026. They illustrate implemented interfaces and one demonstration scenario; they are not observations from the pending usability participants or a sample of the 500 routing texts.

The administrator screenshot shows the destination selected before pressing the forwarding button. Selection alone is not evidence that assignment was saved. The subsequent departmental screen shows the corresponding task in processing, while the citizen screen shows the final departmental decision. The recorded completion concerns the prototype's information-request workflow; it does not demonstrate that a replacement KTP was issued by an actual institution. These screenshots also do not show a rejected cross-department access attempt. The separate API case matrix in Study~3 provides the evidence for the tested access boundaries.

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{images/prototype-01-citizen-form.png}
\caption{Citizen request form with a synthetic lost-KTP inquiry entered before submission. The form records a title and a plain-language description.}
\label{fig:citizen-form}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{images/prototype-02-submitted-request.png}
\caption{Citizen view after submission, showing a request identifier, the initial review status, and a primary department awaiting administrator review.}
\label{fig:submitted-request}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{images/prototype-03-admin-assignment.png}
\caption{Administrator review with a decision note and the population and civil registration department selected. The forwarding button submits the assignment; direct approval is disabled while a destination is selected. ML diagnostics are available in this administrator view.}
\label{fig:admin-assignment}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{images/prototype-04-department-processing.png}
\caption{Departmental staff view showing the request in processing and a completion note prepared before the final decision. The visible task authority applies to the population and civil registration department.}
\label{fig:department-processing}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{images/prototype-05-citizen-result.png}
\caption{Citizen-visible history after the departmental approval, showing review, waiting, processing, and the final decision with its note. The supporting-file section is empty; this figure does not establish that a downloadable result document was supplied.}
\label{fig:citizen-result}
\end{figure}
\clearpage

'''

def update_tex(tex):
    if r'\label{sec:prototype}' in tex:
        return tex
    marker = r'\subsection{Authorization and execution conditions}'
    assert tex.count(marker) == 1, 'Expected one insertion point'
    return tex.replace(marker, FRAGMENT + marker, 1)

if __name__ == '__main__':
    image_dir = PROJECT / 'images'
    image_dir.mkdir(exist_ok=True)
    provenance = []
    for original, target in SHOTS:
        src = SOURCE / original
        dst = image_dir / target
        shutil.copyfile(src, dst)
        digest = hashlib.sha256(dst.read_bytes()).hexdigest()
        assert digest == hashlib.sha256(src.read_bytes()).hexdigest()
        provenance.append({'file': 'images/' + target, 'source_filename': original,
                           'sha256': digest, 'operation': 'unchanged copy'})
    main = PROJECT / 'main.tex'
    main.write_text(update_tex(main.read_text(encoding='utf-8-sig')), encoding='utf-8')
    (PROJECT / 'screenshots-source-map.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print('Added 5 unchanged screenshots, captions, cross-references and provenance.')
