# Setup SGWA pada Windows

Panduan instalasi baru yang lengkap (SQL database/user, migrasi tabel, backend, frontend, worker, dan katalog 25 instansi) ada di [README](../README.md#instalasi-pertama-di-laptop-baru--windows--powershell). Katalog lama dibersihkan dengan `python -m scripts.sync_agency_catalog --apply`, setelah preview dan backup otomatis.

Semua perintah dijalankan dari root proyek kecuali dinyatakan lain. Backend dan frontend berjalan terpisah; Vite mem-proxy `/api` ke port 8000.

## Instalasi pertama

Gunakan Python 3.11+ (proyek ini dikembangkan pada Python 3.12), Node.js 20.19+ atau 22.12+, dan MySQL 8.4. Pastikan `python`, `node`, `npm.cmd`, dan `git` dapat dijalankan.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm.cmd --prefix frontend ci
Copy-Item .env.example .env
```

Lockfile Python berasal dari Windows/Python 3.12. Untuk Python/OS lain gunakan `pip install -e ".[dev]"`, lalu uji kembali sebelum mengganti lockfile. Tidak perlu menjalankan activation script PowerShell.

## Database: EnvKit

EnvKit menyatukan MySQL/MariaDB pada modul layanan, tetapi keduanya engine berbeda. Pilih Oracle MySQL 8.4 jika harus memenuhi ketentuan MySQL secara harfiah. Aktifkan layanan lalu verifikasi server lewat `SELECT VERSION(), @@version_comment` menggunakan client database. Server lokal pada 6 Oktober 2026 telah diverifikasi Oracle MySQL Community 9.7.2.

Koneksi umum: `127.0.0.1:3306`. Jika menggunakan instalasi lokal EnvKit dengan root tanpa password dan belum memiliki database/user `sgwa_demo`, perintah berikut membuat database aplikasi dan database test tersendiri, akun terbatas pada keduanya, serta `.env` dengan secret acak:

```powershell
.\.venv\Scripts\python.exe scripts/setup_envkit.py
```

Script menolak menimpa database/user yang sudah ada. Tidak mengubah `sgwa_db`. Jika root memiliki password, tetapkan `ENVKIT_ROOT_PASSWORD` pada sesi terminal secara lokal sebelum menjalankan; jangan menyimpan password root di repository.

Untuk konfigurasi manual, gunakan user dengan hak hanya pada database aplikasi dan test. Isi `.env`:

```dotenv
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/sgwa_demo
TEST_DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/sgwa_test_codex
```

Percent-encode karakter khusus pada username/password URL. Database test harus berawalan `sgwa_test` dan tidak boleh berisi data yang dibutuhkan. PyMySQL terhubung langsung; client `mysql.exe` yang berasal dari MariaDB pada PATH tidak menentukan engine server.

## Database: Docker MySQL 8.4

Alternatif jika Docker Desktop aktif:

```powershell
docker compose up -d mysql
```

Gunakan port `3307` dan nilai database/user/password lokal dari `.env.example`. Volume `sgwa_mysql` menyimpan data. Script init membuat database test hanya saat volume pertama diinisialisasi. Jangan menghapus volume yang berisi data yang dibutuhkan.

## Konfigurasi lain

- `JWT_SECRET`: buat nilai acak minimal 32 karakter, misalnya dengan `python -c "import secrets; print(secrets.token_urlsafe(48))"` di terminal pribadi.
- `DEMO_PASSWORD`: password lokal minimal 10 karakter. Seed awal membaca ini; seed ulang tidak mengganti akun lama.
- `TRUSTED_ORIGINS`: origin frontend yang benar, default localhost/127.0.0.1 port 5173.
- `COOKIE_SECURE=false` hanya untuk development HTTP lokal. HTTPS memakai true.
- `MODEL_DIR=ml/artifacts`: direktori hasil training.

`.env` diabaikan Git. Jangan menyalinnya ke laporan tugas atau repository publik.

## Migrasi, model, dan seed

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.app.seed
.\.venv\Scripts\python.exe -m scripts.bootstrap_ml
.\.venv\Scripts\python.exe -m scripts.backfill_results
```

Migrasi Alembic adalah sumber skema. Startup API tidak otomatis membuat tabel. Jika model hilang/rusak, endpoint submit memberi 503 dan tidak menyimpan permohonan setengah jadi.

Backfill membuat bukti untuk keputusan final historis secara idempotent. Data sumber tetap dipertahankan; waktu atau catatan yang tidak tercatat ditampilkan sebagai tidak tersedia dan bukti diberi label hasil konversi. Setelah migrasi sesi lama perlu login ulang; seed tidak mengganti password akun yang sudah ada.

## Server

Terminal 1:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
npm.cmd --prefix frontend run dev
```

Buka http://127.0.0.1:5173. Port frontend tetap 5173; bila terpakai, hentikan proses proyek yang lama atau sesuaikan port dan trusted origins bersama-sama. Build melalui `npm.cmd --prefix frontend run build`. Preview build memerlukan pengaturan proxy/server terpisah; perintah `dev` adalah jalur demo yang didokumentasikan.

## Testing

```powershell
.\.venv\Scripts\python.exe scripts/test_backend.py
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run e2e
```

Test backend memuat TEST_DATABASE_URL dari `.env` tanpa mencetak kredensial. Tanpa konfigurasi tersebut, tes database ditandai skipped; itu bukan verifikasi integrasi. E2E memerlukan backend/frontend dan seed aktif serta Edge. Screenshots: `frontend/test-results/`. Tes e2e menambah permohonan dan dinas demo dengan nama unik.

## Troubleshooting

### E2E terisolasi di laptop baru

Tes browser menambah permohonan dan instansi; gunakan schema dan model khusus test. Buat database `sgwa_test_e2e` di MySQL dan beri akun aplikasi akses hanya ke schema test tersebut, lalu salin `.env.e2e.example` menjadi `.env.e2e`. Isi URL, JWT secret test, dan `DEMO_PASSWORD` yang sama dengan `.env` (dibaca tes browser). Jangan commit environment.

Hentikan API biasa di port8000; frontend Vite tetap di5173. Dari root:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_e2e
.\.venv\Scripts\python.exe -m scripts.run_e2e_server
```

Di terminal lain jalankan `npm.cmd --prefix frontend run e2e`. Helper menolak nama schema di luar awalan `sgwa_test` dan model di luar subdirektori `.superpowers`. Tidak mereset schema; fixture sintetis tetap hanya di schema E2E. Setelah tes, hentikan server E2E dan jalankan kembali API biasa agar frontend memakai data aplikasi.

| Gejala | Pemeriksaan |
| --- | --- |
| 503 database | Layanan EnvKit/Compose aktif, URL/port benar, user punya akses |
| 503 model | Pulihkan artefak aktif/rollback; instalasi pertama gunakan bootstrap setelah migrasi dan seed |
| Login gagal | Email akun demo benar; seed pernah berjalan; password akun lama belum berubah |
| 403 origin/CSRF | Buka origin yang diizinkan, muat ulang tab, jangan POST langsung tanpa bootstrap CSRF |
| 409 saat keputusan | Permohonan telah berubah; muat ulang, baca perubahan, putuskan ulang |
| API health tersedia tetapi fitur gagal | Health hanya liveness API; tetap periksa database/migrasi/model |

## Worker SLA (terminal ketiga)

```powershell
.\.venv\Scripts\python.exe -m backend.app.sla.worker
```

Worker memeriksa tugas setiap 60 detik. Untuk satu pemeriksaan gunakan `--once`. Tenggat dihitung dalam hari kalender UTC sejak tugas dibuat; UI menampilkan WIB. Perubahan SLA dinas berlaku untuk tugas baru. Backup aplikasi sebelum forward migration; jangan jalankan downgrade/drop_all pada database aplikasi.

Untuk menghapus fixture Pendidikan yang dibuat tes browser: `python -m scripts.cleanup_education_dummy`. Script memvalidasi kode/nama dan pengajuan fixture; hubungan dengan data lain membatalkan transaksi. Riwayat audit dipertahankan.


## Pembaruan ML 25 kelas

Migrasi `0008`. Setup pertama: migrasi → seed → bootstrap → backfill. Startup ulang mempertahankan versi aktif. Gunakan [panduan ML](ml.md) untuk koreksi, verifikasi, training kandidat, aktivasi dan rollback. Pengajuan baseline saat ini memerlukan review manual admin; confidence minimal70% saja belum cukup untuk mengaktifkan routing otomatis.
