# SGWA — Smart Government Workflow Automation

Web proyek akhir semester dengan klasifikasi permohonan Indonesia menggunakan ML lokal. Warga mengajukan kebutuhan; sistem menyarankan dinas; staf memproses; admin menangani eskalasi. Keputusan layanan tetap manual.

## Stack

Python 3.11+ / FastAPI / SQLAlchemy / Alembic, React + TypeScript + Vite, MySQL 8.4, TF-IDF + Logistic Regression. UI memakai Radix Themes dan Phosphor. Tidak membutuhkan API AI berbayar.

## Jalankan di Windows

Dari root proyek, pastikan MySQL/layanan database EnvKit berjalan dan `.env` sudah diatur:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m ml.train
.\.venv\Scripts\python.exe -m backend.app.seed
```

Terminal backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Terminal frontend:

```powershell
npm.cmd --prefix frontend run dev
```

Web: http://127.0.0.1:5173 · Swagger: http://127.0.0.1:8000/docs

Setup lengkap, termasuk instalasi baru: [docs/setup.md](docs/setup.md). Skenario penilaian: [docs/demo.md](docs/demo.md). Dataset dan batas model: [docs/ml.md](docs/ml.md).

## Akun demo

Password seluruh akun demo awal berada di `DEMO_PASSWORD` dalam `.env` lokal. Tidak dicatat di Git. Seed tidak mengganti password akun yang sudah ada.

| Role | Email |
| --- | --- |
| Warga | warga@demo.sgwa.id |
| Staf Dukcapil | dukcapil@demo.sgwa.id |
| Staf Perizinan | perizinan@demo.sgwa.id |
| Staf Pajak | pajak@demo.sgwa.id |
| Staf Kesehatan | kesehatan@demo.sgwa.id |
| Admin | admin@demo.sgwa.id |

## Pengujian

```powershell
.\.venv\Scripts\python.exe scripts/test_backend.py
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run e2e
```

Backend integration tests hanya memakai database dengan nama berawalan `sgwa_test`. Tes tersebut membersihkan tabel dalam database test. E2E memakai server lokal yang sudah berjalan dan menambah data demo. Browser e2e default: Microsoft Edge terinstal.

## Menambah dinas

Admin dapat menambah dinas dan menugaskan staf tanpa mengubah kode/skema. Dinas baru langsung menerima pengalihan manual. Untuk klasifikasi otomatis: tambah minimal 50 contoh dengan label berupa kode dinas dan minimal lima kelompok skenario, training ulang, lalu restart backend. Prediksi historis tetap disimpan.

## Batas demonstrasi

Dataset awal berisi 200 teks sintetis dari 40 kelompok; evaluasi bukan bukti akurasi pada data warga nyata. Skor model bukan kepastian layanan. Versi ini merutekan satu dinas, tanpa pembayaran, tanda tangan, notifikasi eksternal, atau integrasi pemerintah nyata.

Server lokal EnvKit yang tersedia saat pengembangan teridentifikasi sebagai MariaDB 11.8.2. Pengujian pada server tersebut tidak diklaim sebagai pengujian Oracle MySQL. Konfigurasi MySQL 8.4 melalui Compose disertakan untuk verifikasi syarat database tugas.
