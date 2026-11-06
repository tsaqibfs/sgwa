"""Update the supplied manuscript using only five reported participant records."""
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'paper-routing-study'
SOURCE=Path('C:/Users/Lenovo/.codex/attachments/1ab22e6e-a8a1-43b1-839c-25c8bd89b43a/Pasted text.txt')
MAIN=PROJECT/'main.tex'
text=SOURCE.read_text(encoding='utf-8-sig')
history=PROJECT/'revision-history'
history.mkdir(exist_ok=True)
(history/'pre-five-participants-workspace.tex').write_text(MAIN.read_text(encoding='utf-8-sig'),encoding='utf-8')
(history/'user-supplied-20261028.tex').write_text(text,encoding='utf-8')

seconds=[179,119,169,149,124]
assert sum(seconds)==740 and statistics.mean(seconds)==148 and statistics.median(seconds)==149

old='Participant usability results remain pending.'
new=('A separate exploratory usability observation recorded independent completion for five campus participants, '
     'with a mean reported duration of 2 min 28 s; three commented on the inability to view registration passwords, '
     'and one reported an incorrect category for a wet family-card request. '
     'The task and timing boundaries require clarification before the durations are compared across participants.')
assert text.count(old)==1
text=text.replace(old,new)
text=text.replace('Because routing labels lack independent domain review and usability testing is pending, the conclusions are restricted to synthetic scenarios and selected implementation cases.',
                  'Because routing labels lack independent domain review and the usability observations involve a small campus convenience sample, conclusions are restricted to synthetic scenarios, selected implementation cases, and the reported participant observations.')

old_method=('A separate citizen-interface usability study is planned with eight campus peers as a convenience sample. '
            'Tasks concern submitting a request, finding it again, interpreting status and department, and reading the result. '
            'Planned measures include independent completion, completion with help, elapsed task time, errors, assistance, and comments. '
            'Network or tunnel failures and administrator waiting time must be recorded separately from participant task time. '
            'At manuscript preparation, no participant outcomes, usability scores, or observed staff workload are available. None is inferred from screenshots or automated tests.')
assert text.count(old_method)==1
new_method=r'''A separate exploratory citizen-interface usability observation involved five campus participants as a convenience sample. For each participant, the available record contains an overall completion outcome, one elapsed duration, and an optional comment. All five outcomes were recorded as independent. The available record does not specify the exact task sequence, the start and stop boundaries for timing, whether registration was included in each duration, participant devices, administration conditions, or whether network and officer waiting time were excluded. Consequently, durations are described as reported session times; they are not attributed to any particular task or used as service-processing times. The recorded times written with a dot are interpreted here as minutes and seconds (e.g., 02.59 as 2 min 59 s).

Participants are identified as P1--P5 in the manuscript. Empty comments are reported as no comment recorded, not as proof that participants encountered no difficulty. The record does not supply task-level errors, assistance counts, questionnaire responses, or SUS scores, so these cannot be reconstructed. The earlier proposed task list is a plan, not evidence that every participant completed every task. Observed comments and completion outcomes are reported separately from the synthetic routing pilots. Before final submission, the researchers should document the actual task protocol, timing boundaries, observation conditions, and consent arrangements from their records.'''
text=text.replace(r'\subsection{Reproducibility and pending usability evaluation}',r'\subsection{Reproducibility and usability observation}')
text=text.replace(old_method,new_method)
text=text.replace('the pending usability participants','the usability participants')
text=text.replace('Preserve logs; report limits; keep pending usability separate','Preserve logs and report limits; report usability separately')

marker=r'\subsection{Relationship to the research question and threats to validity}'
assert text.count(marker)==1
USABILITY=r'''\subsection{Exploratory usability observations}\label{sec:usability}
Five campus participants were recorded as completing the observed session independently (5/5). This is the supplied overall outcome; the available data do not establish completion rates for individual tasks. The recorded durations were 2:59, 1:59, 2:49, 2:29, and 2:04, interpreted as minutes and seconds. Their arithmetic mean was 2:28 and median was 2:29, with a range of 1:59--2:59. Because the timing start and stop points and the task sequence are undocumented, these summaries describe the five reported durations only and should not be compared with service-delivery time or presented as a validated task benchmark.

\begin{table}[!htbp]\centering\small
\caption{Exploratory usability observations as reported by five participants. Times are interpreted as minutes:seconds; a dash means no comment was recorded.}\label{tab:usability}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{p{0.10\linewidth}p{0.16\linewidth}p{0.13\linewidth}p{0.45\linewidth}}
\toprule Participant & Overall outcome & Time & Comment summary\\\midrule
P1 & Independent & 2:59 & Registration password could not be displayed for checking.\\
P2 & Independent & 1:59 & --\\
P3 & Independent & 2:49 & Registration password could not be displayed for checking.\\
P4 & Independent & 2:29 & --\\
P5 & Independent & 2:04 & Reported the same password issue and an incorrect housing-category prediction for ``KK basah''.\\
\bottomrule\end{tabular}
\end{table}

Three of five participants commented that they could not view the password during registration. This suggests that a clearly labeled show/hide control deserves consideration; the records do not establish password-entry error rates. One participant reported that a request concerning a wet family card (\emph{Kartu Keluarga}, abbreviated KK) was categorized as housing rather than population/civil registration. The exact full input, model version, score, and final administrator assignment were not included in the observation record, so this is a participant-reported misclassification, not a separately reproduced classifier result or a verified cross-department data disclosure. It illustrates why short everyday wording and the distinction between a recommendation and the final authorized assignment merit further study.

These observations are a small convenience-sample pilot, not a SUS measurement or representative evidence for the broader public or government staff. No assistance counts, task-level errors, system logs, or questionnaire scores were supplied. A subsequent study should record exact tasks, device and network conditions, timing boundaries, and anonymized observations with the participants' consent, and should retain the reported KK example with enough context to reproduce it. No participant names are necessary for the public paper.

'''
text=text.replace(marker,USABILITY+marker)
text=text.replace('Eight planned campus participants would constitute a convenience sample and would not by themselves represent citizens or civil servants generally.',
                  'The five campus participants form a convenience sample and do not represent citizens or civil servants generally; the task and timing protocol needs further documentation.')
text=text.replace('The next empirical step is the planned citizen usability study, reported using actual task observations rather than inferred scores.',
                  'The five-person exploratory observation recorded independent overall completion for all participants, three password-visibility comments, and one participant-reported KK category error; its incomplete timing protocol and small convenience sample limit interpretation.')

count=text.count(r'\newpage')
assert count==4, f'Expected four user-inserted page breaks, got {count}'
text=text.replace(r'\newpage','')
# Keep floats reasonably close to the surrounding text without pinning whole pages.
text=text.replace(r'\raggedbottom',r'\raggedbottom'+'\n'+r'\setlength{\textfloatsep}{10pt plus 2pt minus 2pt}'+'\n'+r'\setlength{\intextsep}{8pt plus 2pt minus 2pt}',1)
assert not re.search(r'\busability (?:results remain|testing is|study is) pending\b|Eight planned campus|no participant outcomes',text,re.I)
assert all(key in text for key in ['tsaqibsoka@it.student.pens.ac.id','mfirman@it.student.pens.ac.id',r'\label{tab:usability}'])
assert all(ord(c)>=32 or c in '\n\t\r' for c in text)
MAIN.write_text(text,encoding='utf-8')
(PROJECT/'USABILITY-NOTES-20261028.txt').write_text('''Pencatatan lima peserta untuk revisi paper

P1: mandiri, 02:59, komentar password tidak dapat dilihat saat daftar.
P2: mandiri, 01:59, tidak ada komentar tercatat.
P3: mandiri, 02:49, komentar password tidak dapat dilihat saat daftar.
P4: mandiri, 02:29, tidak ada komentar tercatat.
P5: mandiri, 02:04, komentar password dan prediksi KK basah ke perumahan.

Interpretasi durasi: tanda titik pada data asli dianggap menit.detik; periksa
makna dan batas waktu bersama peneliti. Rata-rata 2:28; median 2:29; rentang
1:59-2:59. Hasil mandiri adalah status keseluruhan yang dilaporkan, bukan
otomatis berarti setiap tugas berhasil tanpa kesalahan.

Komentar KK basah adalah laporan peserta; teks lengkap, versi/score model,
hasil penugasan akhir dan log tidak diberikan. Tidak dinyatakan direproduksi.
Tidak ada skor SUS, hitungan kesalahan, bantuan, kondisi pengujian atau urutan
tugas per peserta yang dikarang. Nama peserta tidak dimasukkan ke naskah.
Empat perintah newpage manual pada sumber yang ditempel dihapus untuk mengurangi
ruang kosong; FloatBarrier tetap untuk menjaga urutan gambar/tabel.
Sebelum publikasi pastikan persetujuan peserta dan detail protokol tercatat.
''',encoding='utf-8')
print('Updated five anonymized participant records; mean 148 seconds, median 149; removed 4 manual newpage commands.')
