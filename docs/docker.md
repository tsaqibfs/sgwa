# Menjalankan SGWA dengan Docker

Paket ini menjalankan frontend Nginx, API Python, worker SLA, dan **Oracle MySQL 8.4**. Python, Node.js, dan MySQL lokal tidak diperlukan untuk menjalankan container. Pasang Docker Desktop dengan engine Linux aktif dan Docker Compose v2 atau lebih baru. Jalankan semua perintah dari root proyek.

## Setup pertama

Salin contoh environment:

```powershell
Copy-Item .env.docker.example .env.docker
```

Edit `.env.docker` dan ganti seluruh nilai `CHANGE_ME`. Gunakan password MySQL dengan huruf, angka, underscore atau hyphen karena digunakan dalam URL database. `JWT_SECRET` minimal 32 karakter dan `DEMO_PASSWORD` minimal 10 karakter. Jangan membagikan file ini atau memasukkannya ke Git/image.

Jika Python tersedia, alternatifnya jalankan `python scripts/setup_docker_env.py` **tanpa menyalin contoh lebih dulu**. Script menghasilkan empat kredensial acak dan menolak menimpa file yang sudah ada. Password akun demo dapat dilihat pada `DEMO_PASSWORD` di file lokal.

```powershell
docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240
docker compose --env-file .env.docker -f compose.docker.yaml ps -a
```

Build pertama memerlukan internet dan dapat memakan beberapa menit. Jika `docker` atau `docker-credential-desktop` tidak ditemukan di PowerShell Windows, tambahkan folder instalasi untuk sesi tersebut, lalu ulangi:

```powershell
$env:PATH = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:PATH
```

Urutan startup: MySQL sehat → `init` menjalankan Alembic, training ML, seed, dan backfill bukti historis → API dan worker → frontend. Status `init` **Exited (0)** adalah normal. Tabel dibuat otomatis; tidak perlu mengimpor SQL manual. Seed menyediakan 25 instansi resmi dan lima akun: `warga@demo.sgwa.id`, `admin@demo.sgwa.id`, `dukcapil@demo.sgwa.id`, `perizinan@demo.sgwa.id`, `kesehatan@demo.sgwa.id`. Semua akun baru memakai `DEMO_PASSWORD`.

- Frontend: http://localhost:8080
- Swagger API: http://localhost:8001/docs
- Health API: http://localhost:8001/api/v1/health

Browser mengakses API melalui `/api/` pada frontend. Nginx mempertahankan cookie, meneruskan SSE tanpa buffering, dan memperbarui alamat backend melalui DNS Docker ketika container dibuat ulang. MySQL tidak membuka port host. Model tetap memakai empat kelas yang dijelaskan di README; katalog 25 instansi tidak memperluas kelas ML secara otomatis.

## Operasional dan pembaruan

```powershell
# Periksa error startup/migrasi/training
docker compose --env-file .env.docker -f compose.docker.yaml logs --tail 100 init backend worker

# Hentikan container; database dan model tetap tersimpan
docker compose --env-file .env.docker -f compose.docker.yaml down

# Setelah memperbarui kode, bangun dan jalankan kembali
docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240
```

Named volume `sgwa-demo-docker_mysql_data` dan `sgwa-demo-docker_model_data` terpisah dari database EnvKit serta Compose MySQL lama (`compose.yaml`). `init` dapat dijalankan ulang: migrasi ke versi terbaru, model dilatih ulang, katalog di-upsert, akun yang ada tidak diganti passwordnya. Startup tidak menghapus data demo/permohonan yang sudah tersimpan.

Jangan menambahkan `-v` pada `down` kecuali memang ingin **menghapus seluruh database dan model container**. Simpan `.env.docker` selama volume digunakan. Mengubah password MySQL di file environment tidak mengganti password pada database yang sudah diinisialisasi; perubahan akun harus dilakukan di MySQL. Mengubah `DEMO_PASSWORD` juga tidak mengubah password akun yang sudah ada.

Jika port 8080/8001 dipakai aplikasi lain, kosongkan port tersebut atau ubah mapping Compose dan `TRUSTED_ORIGINS` secara konsisten. Jika `init` gagal, baca log dan perbaiki penyebabnya sebelum mengulang `up`. Healthcheck API memeriksa respons HTTP; pemeriksaan alur login/permohonan tetap diperlukan untuk validasi aplikasi.

Paket ini untuk demo lokal: port hanya terikat ke loopback, cookie menggunakan HTTP. Deployment publik membutuhkan HTTPS, pengelolaan secret, akun selain demo, dan pengamanan tambahan sesuai backlog README.

Referensi: [urutan startup Docker Compose](https://docs.docker.com/compose/how-tos/startup-order/) dan [buffering proxy Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering).

## Hasil verifikasi lokal — 9 Oktober 2026

Build backend Python 3.12 dan frontend berhasil. MySQL Community 8.4.11, migrasi `0002`, 25 instansi aktif dan lima akun terverifikasi. API/frontend/MySQL sehat, worker memeriksa SLA, dan `init` selesai dengan exit code 0. Login cookie/CSRF, pemuatan model empat kelas, SSE melalui Nginx, navigasi SPA, serta pengiriman permohonan dengan klasifikasi dan workflow diuji melalui browser Edge. Pengujian API/SSE diulang setelah backend dibuat ulang dan tetap lolos. Permohonan uji dibersihkan dari database container; data EnvKit tidak disentuh.

## Fitur layanan — 10 Oktober 2026

Migrasi terbaru `0007` menambahkan profil/session version, formulir/versi, notifikasi, bukti hasil dan mock checks. Init menyertakan script backfill dan menjalankannya setelah seed; volume lama diperbarui secara additive, password akun lama tetap. Login ulang sesudah migrasi. Bukti tetap untuk demonstrasi akademik, dengan cetak/simpan PDF melalui browser. Lihat [verifikasi fitur layanan](service-features-verification.md) untuk hasil build, pengujian dan batas ML yang masih empat kelas.
