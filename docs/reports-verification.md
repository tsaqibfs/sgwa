# Verifikasi laporan layanan dan CSV

Tanggal: 13 Oktober 2026. Fase ini menambahkan laporan berdasarkan role dan CSV; bukan analytics prediktif atau pembaruan model ML.

## Pengujian

- Backend/ML: 127 tes lulus, tanpa skip, 490,58 detik. Tiga warning yang sudah ada: deprecation Starlette/httpx dan datetime.utcnow di tes migrasi.
- Laporan/CSV: 22 tes lulus, 66,14 detik. Mencakup scope warga/staf/admin, dinas pendamping tanpa duplikasi, filter dan summary, batas 5.000, keamanan formula, error dan audit.
- Tes tambahan isolation: lulus, 11,57 detik. Session laporan memakai REPEATABLE READ ketika engine autentikasi memakai READ COMMITTED; snapshot konsisten saat writer lain commit dan isolation koneksi dipulihkan.
- Pool satu koneksi: kegagalan 503 direproduksi sebelum perbaikan. Auth dan query laporan sekarang berbagi satu session laporan melalui dependency; tes lulus.
- Frontend akhir: 30 tes lulus, 22,39 detik; build lulus, 10,49 detik.
- Edge laporan setelah perbaikan dependency: tiga tes lulus, 34,7 detik. Pengujian mencakup CSV lebih dari satu halaman, formula, keyboard, lebar 375/768/1366, dan error/401 tanpa file palsu.
- Regresi Edge akhir: 22 tes lulus, 5,1 menit; tanpa skip.

## Native dan Docker

Native menggunakan Oracle MySQL Community 9.7.2 di EnvKit. Docker menggunakan MySQL 8.4 terpisah. Schema tetap 0008; tidak ada migrasi atau training baru untuk laporan.

Smoke native dan Docker menguji warga, staf, admin, dinas pendamping, JSON/CSV, 401/403, BOM/formula, no-store, 25 kelas ML dan SSE. Fixture sintetis dibersihkan berdasarkan ID, pemilik dan marker yang diverifikasi. Pemeriksaan terakhir setelah perbaikan pool lulus di native :8002 dan Nginx :8080.

Snapshot native sebelum pembaruan dibandingkan setelah smoke: hash/count seluruh tabel selain audit sama; audit lama identik, audit ekspor baru boleh bertambah. Pointer model, revision dan kandidat tidak berubah. Backup SQL native privat disimpan di lokasi backup proyek.

Snapshot Docker pertama sebelum rebuild gagal karena layanan MySQL belum hidup. Rebuild sudah mulai sebelum hasil kegagalan dibaca, sehingga identitas seluruh baris sebelum rebuild pertama tidak dapat dibuktikan. Baseline valid dibuat setelah rebuild pertama; smoke dan startup berikutnya, termasuk rebuild perbaikan pool, mempertahankan seluruh hash/count tabel, pointer/revision, kandidat dan audit lama. Worker dihentikan selama perbandingan, lalu diaktifkan kembali. Tidak memakai down -v atau reset database.

## Kontrak dan batas

Filter tanggal mengikuti tanggal pengajuan WIB, inklusif; ISO YYYY-MM-DD wajib. Scope diterapkan sebelum count, summary, halaman dan CSV. CSV berisi seluruh hasil filter, maksimal 5.000; lebih banyak menghasilkan 413, tidak dipotong. Ekspor kosong tetap memiliki header. Confidence adalah skor prediksi historis, bukan akurasi.

Selesai mencakup approved dan rejected. Durasi rata-rata hanya hasil final dengan durasi valid. Nilai yang tidak tersedia ditampilkan sebagai —. Audit report.export_prepared membuktikan server menyiapkan ekspor, bukan pengguna menyimpan file. NIK, email, dokumen, isi permohonan dan catatan internal tidak diekspor. API laporan memakai no-store. Snapshot setiap HTTP request konsisten; request JSON dan unduhan terpisah dapat melihat perubahan yang terjadi di antaranya.

Analytics prediktif, laporan coverage, CI, TLS/rate limiting dan load test tetap backlog. Data evaluasi ML sintetis tetap untuk demo; fase ini tidak mengklaim peningkatan kualitas model.

## Keputusan pelaksanaan

Berikut seluruh keputusan dari ledger fase ini, dengan biaya bila salah.

```text
Ruling: Keep approved feature checkout — existing clean feat/sgwa-demo and approved plan preserve it — cost: changes share the checkout.
Ruling: Use Python bookkeeping instead of Bash helpers on Windows — same ledger/brief contract — cost: manual verification of parity.
Task2 focused18 passed59.03s; baseline105 passed511.70s/3 existing warnings. Ruling: Pipeline independent frontend Task3 while whole backend regression runs — report/CSV interfaces already proven and frontend cannot alter that run — cost: task completion order differs; Task2 remains pending until whole suite green.
Task3: Ruling: Use .test.tsx for API tests rather than .test.ts — existing Vitest include only src/**/*.test.tsx — cost: planned test paths changed; config preserved. Initial no-tests discovery was not RED evidence; product additions removed and RED repeated with corrected paths.
Task4: Ruling: Move existing E2E screenshots from deleted older plan namespace to standard frontend/test-results — whole-suite execution must not recreate another plans scratch — cost: three existing test fixture paths changed, product behavior unchanged.
Task5: Ruling: Docker first pre-rebuild snapshot unavailable — initial MySQL service was stopped and no-deps snapshot failed DNS; rebuild had already begun before its final output was read — validate current state then compare second startup — cost: cannot prove full Docker row identity before first rebuild; native pre-upgrade snapshot/backup remain available. No application migration was introduced.
Task5: Ruling: Reuse existing get_current_user/require_role inside report RR dependency instead of opening separate auth and report connections — single-pool test reproduced503 due self-exhaustion — cost: report-specific dependency must preserve auth behavior; old endpoints/isolation unchanged. RED single-connection test observed10.06s.
Task5: Ruling: Stage Docker startup with worker stopped until row-hash comparison instead of single all-service up — avoids SLA writes while measuring preservation — cost: deployment verification uses two startup steps; worker resumed after comparison.
Final: Ruling: Existing catalog-name seed and result backfill remain outside reports changes — they predate this branch; preservation evidence covers observed baseline only, not every possible database — cost: a different preexisting database may change during ordinary init; no universal byte-identity guarantee.
Final: Ruling: Reviewer did not independently rerun private deployment snapshots or test suites — executor read successful actual outputs and hash comparisons; reviewer inspected code/tests/recorded evidence read-only — cost: verification evidence has one execution witness, not an independent rerun.
```

## Review akhir

Satu reviewer fresh-context gpt-6-astra memeriksa perubahan f5f00f2..0a75004 secara read-only, spec, plan, test dan lima Review Focus. Hasil: Critical 0, Important 0, Minor 0; tidak diperlukan fix pass. Reviewer tidak mengulang tes atau mengakses snapshot privat. Tidak ada minor yang ditunda dalam fase laporan ini.

Seed nama katalog dan backfill bukti hasil merupakan perilaku startup yang sudah ada sebelum fase laporan. Hasil snapshot berlaku pada database yang diamati; bukan jaminan bahwa semua kondisi database lain selalu identik setelah init.

Native dikembalikan ke port 8000 dengan database EnvKit; smoke final lulus. Worker native dan Docker kembali aktif setelah perbandingan snapshot, sehingga perubahan SLA berikutnya merupakan aktivitas normal worker. Branch feat/sgwa-demo dipertahankan lokal tanpa merge/push.
