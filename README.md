# SGWA — Smart Government Workflow Automation

Web proyek akhir semester untuk klasifikasi permohonan dengan ML lokal dan workflow paralel antar dinas. Backend dan frontend terintegrasi. Katalog terbaru berisi **25 dinas/badan** sesuai daftar pengguna; nama dan kode lengkap ada di [catalog.py](backend/app/agencies/catalog.py).

## Status terhadap PRD

Sudah tersedia: registrasi/login; role citizen/staff/admin; pengajuan teks; TF-IDF + Logistic Regression; routing ke beberapa dinas; keputusan per dinas; eskalasi confidence rendah, penolakan dan SLA; review admin; SSE; audit; manajemen dinas/staf; editor routing dan SLA; Swagger/OpenAPI; profil/ganti password dengan pencabutan seluruh sesi; form builder dan jawaban versi historis; notifikasi persisten; bukti hasil dengan snapshot/cetak; mock API sintetis.

Model **25 kelas**, normalisasi singkatan, cross-validation berbasis kelompok, koreksi/verifikasi admin, training kandidat, aktivasi dan rollback sudah tersedia. Masih backlog: laporan/CSV, analytics prediktif, coverage, CI, TLS/rate limiting dan load test. Review final dilakukan admin; password Argon2; worker Python/MySQL tanpa Redis/Celery.

Dataset berisi **2.500 contoh sintetis** dengan 25 kode katalog resmi. Holdout menghasilkan macro-F1 **0,546**, di bawah target0,85. Validasi belum memiliki cukup contoh accepted pada confidence minimal70%: **routing otomatis nonaktif**, sehingga pengajuan masuk review admin sambil menampilkan rekomendasi ML. Skor ini belum mengukur akurasi data warga nyata.

Migrasi terbaru `0008` menambahkan feedback, registry dan aktivasi ML. Lihat [Model ML](docs/ml.md), [verifikasi ML](docs/ml-feedback-verification.md), dan [verifikasi fitur layanan](docs/service-features-verification.md). Prediksi lama dan bukti hasil demonstrasi tetap dipertahankan.

## Instalasi dengan Docker (alternatif lengkap)

Untuk menjalankan seluruh aplikasi tanpa memasang Python, Node.js dan MySQL lokal, gunakan [panduan Docker](docs/docker.md). Paket `compose.docker.yaml` menyediakan frontend di **localhost:8080**, API/Swagger di **localhost:8001**, worker SLA, dan MySQL 8.4. Migrasi tabel, training ML dan seed 25 instansi berjalan otomatis. Database container terpisah dari EnvKit dan `compose.yaml` lama.

## Instalasi pertama di laptop baru — Windows / PowerShell

### 1. Prasyarat dan dependensi

Pasang Python 3.11+ (disarankan 3.12), Node.js 20.19+ atau 22.12+, dan **Oracle MySQL**. MySQL 8.4 adalah referensi PRD; pengembangan sebelumnya teruji di MySQL Community 9.7.2. EnvKit boleh digunakan dengan layanan MySQL. Ambil proyek melalui Git atau ekstrak ZIP, lalu buka PowerShell di folder yang berisi README ini. Semua perintah dijalankan dari root tersebut.

```powershell
python --version
node --version
npm.cmd --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm.cmd --prefix frontend ci
Copy-Item .env.example .env
```

Jangan menyalin `.venv`, `node_modules`, `.env` atau backup pribadi dari laptop lain. Jangan menimpa `.env` yang sudah dikonfigurasi. Pada Python/OS berbeda, jika lockfile tidak kompatibel gunakan `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`, lalu uji kembali. Tidak perlu activation script.

### 2. Setup MySQL: database dan user

Start MySQL di EnvKit/MySQL service. Login sebagai administrator melalui client:

```powershell
mysql -h 127.0.0.1 -P 3306 -u root -p
```

Jika `mysql` tidak ada di PATH, gunakan path lengkap `mysql.exe` atau SQL editor MySQL Workbench/EnvKit. Masukkan password root pada prompt lokal. Untuk **instalasi baru**, jalankan SQL berikut setelah mengganti `GANTI_PASSWORD_DB`:

```sql
SELECT VERSION(), @@version_comment;
CREATE DATABASE sgwa_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE sgwa_test_codex CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sgwa_user'@'127.0.0.1' IDENTIFIED BY 'GANTI_PASSWORD_DB';
GRANT ALL PRIVILEGES ON sgwa_demo.* TO 'sgwa_user'@'127.0.0.1';
GRANT ALL PRIVILEGES ON sgwa_test_codex.* TO 'sgwa_user'@'127.0.0.1';
```

`sgwa_demo` untuk aplikasi; `sgwa_test_codex` khusus tes yang akan membersihkan tabelnya. Jika schema/user sudah ada, gunakan konfigurasi yang sesuai tanpa menghapusnya. Hasil version/comment harus menunjukkan MySQL, bukan MariaDB.

### 3. Isi `.env`

```dotenv
DATABASE_URL=mysql+pymysql://sgwa_user:GANTI_PASSWORD_DB@127.0.0.1:3306/sgwa_demo
TEST_DATABASE_URL=mysql+pymysql://sgwa_user:GANTI_PASSWORD_DB@127.0.0.1:3306/sgwa_test_codex
JWT_SECRET=GANTI_DENGAN_SECRET_ACAK_MINIMAL_32_KARAKTER
TRUSTED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
COOKIE_SECURE=false
MODEL_DIR=ml/artifacts
DEMO_PASSWORD=GANTI_PASSWORD_DEMO_MINIMAL_10_KARAKTER
```

Buat JWT secret dengan `.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"` dan salin hasil ke `.env`. Password demo berbeda dari password MySQL. Karakter khusus pada password URL harus di-percent-encode. Sesuaikan kedua URL jika port berbeda: contoh bawaan `.env.example` memakai **3307** untuk Compose, sedangkan setup lokal di atas memakai **3306**. `.env` tidak masuk Git dan tidak boleh dibagikan.

### 4. Buat tabel, model ML, dan data awal

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.app.seed
.\.venv\Scripts\python.exe -m scripts.bootstrap_ml
.\.venv\Scripts\python.exe -m scripts.backfill_results
```

**Alembic membuat seluruh tabel MySQL otomatis.** Tabel aplikasi: `agencies`, `users`, `requests`, `classification_results`, `request_workflows`, `workflow_routes`, `request_events`, `audit_logs`, ditambah `alembic_version`. Tidak perlu membuat tabel satu per satu. Startup API tidak otomatis membuat tabel. Jangan gunakan `drop_all` pada database aplikasi.

Bootstrap pertama membuat `ml/artifacts/versions/<id>/` dan mengaktifkan model awal. Startup berikutnya mempertahankan model pilihan admin tanpa training ulang. Model empat kelas lama disalin ke archive; prediksi historis tetap. Seed menambahkan 25 instansi dan akun demo; seed ulang mempertahankan ID, SLA, akun dan password lama. Nama katalog diperbarui sesuai daftar. Seed tidak melakukan penghapusan data lama; gunakan langkah upgrade di bawah untuk membersihkan dummy.

### 5. Jalankan backend, frontend, dan worker

Buka tiga terminal, semuanya di root proyek.

Terminal 1 — backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```powershell
npm.cmd --prefix frontend run dev
```

Terminal 3 — worker SLA:

```powershell
.\.venv\Scripts\python.exe -m backend.app.sla.worker
```

Web: http://127.0.0.1:5173/ · Swagger: http://127.0.0.1:8000/docs · Health: http://127.0.0.1:8000/api/v1/health

Vite mem-proxy `/api` ke backend 8000. MySQL harus berjalan saat aplikasi digunakan. Worker memeriksa setiap 60 detik; `--once` untuk pemeriksaan sekali. SLA berupa hari kalender; perubahan target tidak mengubah tenggat tugas lama. Health hanya liveness API, bukan bukti database/model siap.

### 6. Akun demo dan smoke test

Password akun awal mengikuti `DEMO_PASSWORD` pada seed pertama:

| Role | Email |
| --- | --- |
| Admin | admin@demo.sgwa.id |
| Warga | warga@demo.sgwa.id |
| Staf Dukcapil | dukcapil@demo.sgwa.id |
| Staf Perizinan / DPMPTSP | perizinan@demo.sgwa.id |
| Staf Kesehatan | kesehatan@demo.sgwa.id |

Login admin dan periksa Dinas & layanan berisi 25 instansi. Staf untuk 22 instansi lain dibuat melalui Manajemen staf. Login warga, ajukan pengurusan KTP; admin meninjau dan mengalihkan ke Dukcapil sebelum staf memproses. Demo paralel: admin memilih Perizinan dan Kesehatan sebagai pendamping saat review. Kedua staf harus menyetujui agar status agregat Disetujui. Ini simulasi koordinasi akademik. [Panduan demo](docs/demo.md).

## Upgrade katalog pada database lama

Hentikan backend dan worker selama pembersihan. Pastikan `.env` menunjuk database aplikasi yang benar:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m scripts.sync_agency_catalog
.\.venv\Scripts\python.exe -m scripts.sync_agency_catalog --apply
.\.venv\Scripts\python.exe -m backend.app.seed
.\.venv\Scripts\python.exe -m scripts.bootstrap_ml
.\.venv\Scripts\python.exe -m scripts.backfill_results
```

Sync tanpa `--apply` menampilkan preview dan rollback. `--apply` membuat backup SQL penuh di `.superpowers/backups/` sebelum menerapkan satu transaksi. Backup mengandung data privat; jangan dibagikan. Untuk pemulihan, uji backup pada schema terpisah yang kosong sebelum memulihkan aplikasi.

Pembersihan mengenali Badan Pendapatan Daerah lama (`pajak`) dan fixture `Dinas Pendidikan Demo` berakhiran timestamp. Pengajuan warga demo terkait, tugas, klasifikasi, riwayat pengajuan dan staf demo terkait ikut dihapus. Riwayat lain tetap valid; aktor staf yang dihapus menjadi anonim. Jika ada akun/pengajuan non-demo terkait, transaksi dihentikan. Instansi tambahan pengguna tidak dianggap dummy otomatis. ID dan SLA Dukcapil/Kesehatan/Perizinan tetap.

## Pengujian dan build

Pastikan `TEST_DATABASE_URL` adalah schema terpisah bernama `sgwa_test...`:

```powershell
.\.venv\Scripts\python.exe scripts/test_backend.py
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
```

Backend tests membersihkan database test. Build menghasilkan `frontend/dist`; `dev` adalah cara demo lokal dengan proxy, bukan deployment produksi. Dengan kedua server berjalan dan Microsoft Edge terpasang:

```powershell
npm.cmd --prefix frontend run e2e
.\.venv\Scripts\python.exe -m scripts.cleanup_education_dummy
```

E2E menambahkan data demo pada database aplikasi, termasuk fixture Pendidikan. Jalankan di demo/salinan DB. Cleanup menghapus fixture yang dikenali, bukan DINAS PENDIDIKAN resmi. Screenshots: `frontend/test-results/`.

## Troubleshooting

| Gejala | Pemeriksaan |
| --- | --- |
| MySQL error 2003 | Start MySQL, cocokkan host/port `.env`. |
| Access denied / 1045 | Cocokkan user/password/host grant; password demo bukan password DB. |
| Unknown database / tabel tidak ada | Buat schema, lalu jalankan Alembic upgrade head. |
| Model 503 | Jalankan training dan restart backend. |
| Login demo gagal | Jalankan seed; perubahan DEMO_PASSWORD tidak mengganti password akun lama. |
| Port 5173/8000 terpakai | Periksa server proyek sebelumnya. |
| 403 CSRF/origin | Gunakan URL frontend yang diizinkan, muat ulang tab. |
| 409 keputusan | Refresh detail dan buat keputusan/konfirmasi baru. |
| Instansi baru belum dirutekan AI | Tambah dataset berlabel/retrain atau gunakan pengalihan admin. |

## Bukti dan batas

[Verifikasi tahap pertama](docs/phase-one-verification.md) adalah bukti historis, bukan pengujian setiap laptop. Dataset awal berisi 200 teks sintetis; macro-F1 1,00 berasal dari 40 contoh uji sintetis. Belum ada klaim kualitas pada data warga nyata, load test 1.000 pengguna, integrasi pemerintah produksi, pembayaran, atau tanda tangan tersertifikasi.

Dokumen: [setup](docs/setup.md), [ML](docs/ml.md), [demo](docs/demo.md), [verifikasi](docs/verification.md).

Verifikasi pembaruan katalog dan panduan instalasi: [catalog-verification.md](docs/catalog-verification.md).
