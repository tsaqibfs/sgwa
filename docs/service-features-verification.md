# Verifikasi fitur layanan SGWA — 10 Oktober 2026

Tahap A menambahkan profil/ganti password, formulir versi, notifikasi persisten, snapshot bukti hasil dan simulasi API pada backend serta frontend. Migrasi terbaru adalah `0007`. Rencana: [service features](superpowers/plans/2026-10-10-sgwa-service-features.md); cakupan: [desain tahap A](superpowers/specs/2026-10-10-sgwa-service-features-design.md).

## Lingkungan dan hasil

| Pemeriksaan | Hasil aktual |
| --- | --- |
| Backend/ML pada schema test terpisah, Oracle MySQL 8.4 | 74 passed, tanpa skipped, 277,77 detik |
| Migrasi kosong serta upgrade `0002` → `0007`, seed/backfill diulang | 2 passed; ID, hash password, workflow dan audit terjaga; termasuk dalam suite 74 |
| Edge headless, frontend Vite/API lokal dengan schema E2E terpisah | 13 passed, 2,8 menit |
| Build TypeScript/Vite | Exit 0; 4859 modul; JS 447,40 kB sebelum gzip |
| Docker Compose lengkap | MySQL/API/frontend sehat, worker aktif, init Exited (0), migrasi `0007` |
| API melalui Nginx 8080 | Cookie/CSRF, 25 instansi, model 4 kelas, form submit, notifikasi, SSE, mock, snapshot final dan read-all lolos |
| Edge melalui Nginx 8080 | Formulir, jawaban historis, riwayat simulasi, bukti immutable dan print media lolos |
| MySQL EnvKit | MySQL Community 9.7.2; backup sebelum upgrade; migrasi `0007`; seluruh baris lama dibandingkan dan tetap utuh; 25 instansi aktif, 5 akun |

Schema backend test dan E2E terpisah dari EnvKit serta Docker demo. Fixture unik untuk verifikasi container beserta relasinya dibersihkan setelah pengujian; data lain dipertahankan. Backup native disimpan lokal di `.superpowers/backups/`, tidak masuk Git.

## Perilaku yang diuji

- Perubahan profil menolak role/email/dinas. Ganti password memeriksa hash terkunci dan mencabut dua sesi, termasuk HTTP, bootstrap CSRF dan SSE. JWT tanpa versi ditolak.
- Form memvalidasi enam tipe, required/optional, key, opsi, tanggal dan rentang. Publikasi/edit bersamaan dilindungi versi dan lock. Konflik submit mengembalikan 409; UI mempertahankan jawaban untuk ditinjau. Jawaban/schema historis tetap setelah publikasi baru. Pengajuan teks tetap tersedia; ketidaksesuaian form/ML masuk review.
- Notifikasi tersimpan bersama request/task/timeline/audit. Kegagalan insert membatalkan transaksi. Scope/read/pagination, penugasan ulang, penerima nonaktif, dua keputusan bersamaan, retry dan worker SLA berulang diuji. SSE hanya memakai notifikasi milik actor. Inbox bertahan setelah login ulang.
- Bukti approved/rejected menyimpan nomor/snapshot unik. Perubahan nama pemohon/dinas tidak mengubah bukti. Backfill diulang aman dan tidak mengarang waktu/catatan yang hilang. Akses lintas pemilik/dinas dan request non-final ditolak. Print menyembunyikan navigasi/tombol serta mempertahankan label demonstrasi.
- Mock memakai fixture lokal untuk tiga jenis × tiga skenario. Citizen dan staf tanpa scope ditolak. Key berbeda payload/request ditolak 409. Retry bersamaan atau respons hilang menghasilkan satu rekaman. Mock tidak menaikkan versi/status request.
- Layout diperiksa pada 375/768/1366 piksel; cetak dengan nama instansi panjang diperiksa secara visual.

Startup Docker pertama menemukan script backfill belum disalin ke image; Dockerfile diperbaiki, rebuild dan startup ulang lolos. Tiga warning suite adalah deprecation Starlette/httpx serta dua penggunaan datetime.utcnow pada tes lama; tidak ada kegagalan/skipped.

## Mengulang verifikasi

Gunakan `TEST_DATABASE_URL` hanya pada schema test yang berawalan `sgwa_test`. Tes akan menghapus tabel schema tersebut. Backend/ML:

```powershell
.\.venv\Scripts\python.exe scripts/test_backend.py
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run e2e
```

E2E memerlukan backend/frontend, lima akun seed, model dan Edge; `.env` harus memiliki `DEMO_PASSWORD` yang sesuai server E2E. E2E membuat fixture unik; jalankan pada database demo pengujian terpisah. Untuk startup container:

```powershell
docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240
docker compose --env-file .env.docker -f compose.docker.yaml ps -a
```

Setup native harus menjalankan migrasi, training, seed dan `python -m scripts.backfill_results` seperti [panduan setup](setup.md). Sesi lama perlu login ulang; seed mempertahankan password.

## Batas tahap A

Model masih **empat kelas** (`dukcapil`, `perizinan`, `kesehatan`, `pajak`), dengan data/evaluasi sintetis. Katalog 25 instansi tidak berarti 25 kelas ML. Training 25 kelas, cross-validation dan retraining batch dari koreksi admin belum diimplementasikan pada tahap ini. Laporan/CSV, forecast, coverage, CI, TLS/rate limiting dan load test tetap tahap B/C pada [roadmap](superpowers/specs/2026-10-10-sgwa-completion-roadmap.md).

Bukti dicetak/disimpan PDF oleh browser; label wajib **Bukti hasil demonstrasi akademik — bukan dokumen resmi**. Mock adalah simulasi lokal. Belum ada PDF server, tanda tangan resmi atau integrasi sistem pemerintah.
