# Prakiraan volume dan verifikasi deployment SGWA

- [x] Hitung volume permohonan per dinas dari tugas utama maupun pendamping. Gunakan hari lengkap WIB, sedikitnya 60 hari kalender, dan maksimal 120 hari riwayat. Bandingkan rata-rata tujuh hari dengan baseline hari yang sama minggu sebelumnya pada dua minggu historis. Sajikan prakiraan tujuh hari, MAE historis, dan keadaan data belum cukup.
- [x] Tambahkan endpoint laporan untuk admin dan staf sesuai dinas, serta pemilihan dinas untuk admin di laporan layanan. Uji cakupan akses di API.
- [x] Tambahkan CI MySQL 8.4 dengan migrasi, coverage, build frontend, dan uji singkat Compose. Gunakan skema dan kredensial CI.
- [x] Tambahkan HTTPS lokal pilihan dan pembatasan laju Nginx untuk autentikasi dan mutasi. Batasi SSE per IP di Nginx dan per akun di API.
- [x] Sediakan skenario k6 dan konfigurasi project Compose terisolasi.
- [x] Jalankan skenario k6 pada Docker dan catat metrik aktual.
