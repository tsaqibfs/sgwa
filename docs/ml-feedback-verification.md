# Verifikasi ML 25 kelas dan feedback admin

Tanggal: 11 Oktober 2026. Branch lokal `feat/sgwa-demo`; tidak merge/push. Spec: [ML dan feedback](superpowers/specs/2026-10-10-sgwa-ml-feedback-design.md), [rencana implementasi](superpowers/plans/2026-10-10-sgwa-ml-feedback.md).

## Hasil dan batas ML

Dataset2.500 contoh sintetis, tepat25 kode katalog. Training2.000/200 kelompok, holdout500/50 kelompok tetap. Lima fold StratifiedGroupKFold, pipeline fit ulang setiap fold. Normalizer `id-v1` mempertahankan negasi/lokasi.

| Ukuran baseline | Hasil aktual |
| --- | --- |
| Macro-F1 holdout sintetis | 0,5463865546 |
| Mean macro-F1 CV | 0,6216546714 |
| Std macro-F1 CV | 0,0647516102 |
| Threshold | 0,70 |
| Accepted OOF | 2 dari2.000 |
| Precision accepted | 1,00 pada2 contoh saja |
| Coverage OOF | 0,10% |
| Routing otomatis | Nonaktif: minimal25 accepted belum tercapai |

Target0,85 belum tercapai. Semua pengajuan baseline masuk review admin meskipun confidence tinggi. Model tetap menampilkan25 probabilitas. Evaluasi sintetis tidak mengukur akurasi warga nyata; data nyata belum tersedia. Training ulang tidak menjamin peningkatan. Multi-label, mapping urusan, NER/lokasi dan branding Lamongan belum dibuat.

## Bukti pengujian

- Seluruh backend/ML terakhir: **105 passed**, zero skips, 451,12detik pada MySQL8.4 terisolasi. Tiga warning dependensi/datetime lama dicatat, tanpa kegagalan.
- Frontend: **12 passed**, 6file, 11,15detik; build produksi berhasil9,15detik.
- Suite Edge lengkap: **19 passed**, 5,0menit. Alur: role, draft/sesi, workflow multi-dinas/manual review, notifikasi, formulir, mock API, bukti cetak, ML correction/review/candidate/activation/rollback, konflik409 dan keputusan final historis.
- Migration/bootstrap populated0007: **2 passed**, 36,70detik; data lama termasuk prediksi Pajak/hasil final tetap setelah upgrade0008 dan bootstrap dua kali, lalu downgrade test.
- Regresi pembulatan JSON MySQL: tes gagal sebelum perbaikan, kemudian lolos. Validasi registry membolehkan selisih float maksimal1e-15; tipe, key, teks, ID dan checksum file tetap diperiksa persis. Perubahan skor0,001 tetap ditolak. Registrasi versi sama juga idempotent setelah roundtrip JSON.
- Screenshot375/768/1366: form feedback, evaluasi25kelas dan daftar versi; body tidak overflow, confusion matrix bergulir dalam panel. Screenshot mobile diperiksa visual.

Workflow backend memakai fixture inference yang secara eksplisit mengaktifkan routing untuk menguji proses staf secara terpisah. Tes runtime menggunakan model asli; browser memakai policy asli dan admin manual-route. Angka test tidak membuktikan coverage ML atau performa beban.

## Native EnvKit

Engine diverifikasi langsung: **Oracle MySQL Community9.7.2**, bukan MariaDB. API/worker dihentikan saat migrasi. Backup SQL privat dibuat sebelum upgrade; dipulihkan pada schema MySQL8.4 test terpisah untuk membandingkan data secara semantik. Semua baris aplikasi lama tetap, audit aktivasi bersifat tambahan. Backup disimpan di `.superpowers/backups/`, tidak masuk Git.

Migrasi0008 dan bootstrap25berhasil. Bootstrap berikutnya mempertahankan `ml25-4bb961bc5928e05b937a1be5`, revision1. File lama disalin ke archive; prediksi historis tidak ditulis ulang. Smoke HTTP: login cookie/CSRF, metadata25, labels, feedback, registry, evaluation dan SSE. Smoke pengajuan baru→review manual→koreksi admin→verifikasi berhasil; hasil klasifikasi tidak berubah. Fixture smoke dibersihkan berdasarkan ID, nama UUID, pemilik demo dan alasan khusus; tidak ada penghapusan umum.

## Docker

Image backend/frontend dibangun ulang; MySQL8.4, backend/frontend sehat, worker berjalan dan init **Exited(0)**. Migrasi0008,25instansi aktif,25kelas dan checksum model terverifikasi. Startup ulang mempertahankan pointer aktif/revision1. Login/CSRF, registry/evaluation/feedback dan SSE diuji melalui Nginx `http://127.0.0.1:8080`; Swagger di8001. Database/volume terpisah dari EnvKit.

Docker init: migrasi→seed→bootstrap→backfill. Training manual memakai service init dengan command override, menghasilkan kandidat tanpa mengganti model aktif. Backend membaca volume model read-only. Pemulihan model rusak memerlukan backup/rollback, tanpa retraining otomatis.

## Reproduksi

Lihat [setup](setup.md), [Docker](docker.md) dan [operasi ML](ml.md). E2E di laptop baru memakai `.env.e2e.example`, `python -m scripts.prepare_e2e`, `python -m scripts.run_e2e_server`, lalu tes frontend. Helper menolak schema aplikasi dan lokasi artefak aplikasi; setup dua kali diuji. Environment, backup dan semua artefak runtime diabaikan Git.

Helper E2E resmi diuji pada schema baru: persiapan dua kali mempertahankan model, dua alur browser ML lolos1,2menit. API EnvKit dikembalikan ke8000; HTTP smoke ulang lolos dan worker melaporkan0 eskalasi SLA.

Laporan/CSV, analytics prediktif, coverage report, CI, TLS/rate limiting dan load test tetap backlog. Laporan ini tidak menyatakan semua scope PRD selesai.


## Review akhir

Satu reviewer fresh-context gpt-6-astra memeriksa seluruh range `7ca4154..cca7d6b` secara read-only. Tidak ada Critical/Important; tiga Minor diregrade tetap Minor dan ditunda sesuai executing-plans. Reviewer tidak mengulang tes: bukti eksekusi berasal dari hasil author di atas. Tidak ada merge/push.

### Keputusan eksekusi beserta biaya/risiko

- Ruling: Preserve approved feature checkout rather than create worktree — user continues established checkout and approved Global Constraints — cost: local edits share checkout; clean status verified.
- Ruling: Use Python bookkeeping on Windows instead of Bash skill helpers — existing environment uses PowerShell — cost: ledger parity requires explicit checking.
- Task1: Ruling: Commit dataset and trainer together with Task2 — expanded CSV causes two existing training tests to fail (extra metadata columns) — cost: one less granular commit; regression retained and fixed before completion.
- Tasks3-4: Ruling: Deliver schema and feedback API together after89-test regression — both participate in new transaction tests — cost: less granular commit. Dedicated sgwa_test_ml_feedback schema enables independent tests without touching baseline test schema.
- Task6: Ruling: Workflow tests inject explicit routing-enabled inference fixture while registry tests use genuine model — OOF policy correctly disables automatic routing due only2 accepted examples, so staff workflow requires controlled accepted classification — cost: workflow tests do not measure real routing coverage; ML/runtime tests do.
- Tasks5-6: Ruling: Commit candidate registry and activation/runtime together after105-test regression — both share registry.py and integrity checks — cost: less granular history; targeted tests retain separation.
- Task8: Ruling: Add public isolated E2E environment/helpers beyond the private fixture paths — new ML browser training must be reproducible on classmates laptops and never target application data — cost: one more environment/setup path to maintain; guards reject non-test schema and application artifact directory.
- Final: Ruling: Accept synthetic generalization limitation and unmet0.85 target — approved scope requires truthful scores and automatic routing disabled when validation insufficient — cost: target quality and real-world accuracy remain unproven.
- Final: Ruling: Keep online learning/multi-label/NER/reporting/CI/TLS/load testing deferred — current approved plan is ML25 plus verified feedback and manual activation — cost: broader PRD scope remains incomplete.
- Final: Ruling: Retain trusted-local-joblib boundary — no artifact upload and only operator-local training is supported — cost: malicious operator-authored pickle can execute code; file integrity is not an adversarial sandbox.

### Minor ditunda

- Successful repeat training leaves redundant staging directories (scripts/train_candidate.py:38-45).
- Bootstrap preservation test reuses same content ID instead of a distinct admin-selected model (backend/tests/test_ml_bootstrap.py:22-30); runtime preserves non-null pointer before any training.
- UI Asal training provenance counts include holdout rows; training count separately remains2000 (ml/train.py:89).
