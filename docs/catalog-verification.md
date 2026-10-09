# Verifikasi katalog dan setup — 9 Oktober 2026

Katalog aplikasi pada Oracle MySQL Community 9.7.2 sudah cocok persis dengan 25 nama yang diberikan pengguna. Semuanya aktif. ID Dukcapil 1, Perizinan 2, Kesehatan 4 dipertahankan bersama SLA yang sudah ada. Seed menambahkan katalog yang sama pada instalasi baru dan tidak lagi membuat Badan Pendapatan Daerah/staf Pajak.

Transaksi aplikasi menambahkan 22 instansi, memperbarui tiga nama, menghapus satu instansi lama, enam pengajuan demo terkait, dan satu akun staf. Tugas, klasifikasi, event serta audit pengajuan yang dihapus ikut dibersihkan. Riwayat lainnya dipertahankan; referensi aktor staf yang dihapus dibuat anonim. Data non-demo terkait menyebabkan transaksi ditolak. Instansi tambahan pengguna di luar pola dummy yang dikenal tidak dihapus otomatis.

Backup SQL dibuat sebelum transaksi pada `.superpowers/backups/before-agency-catalog-20261009-030429-729054.sql` dan tidak masuk Git. Backup berisi data privat; gunakan schema kosong terpisah untuk uji pemulihan.

Hasil pengujian: 45 tes backend dan 2 tes ML lulus pada schema test terpisah, serta 8 tes browser Edge lulus pada aplikasi. Tes baru membuktikan penghapusan data demo, perlindungan akun non-demo, preservasi ID/SLA, dan seed berulang tanpa duplikasi atau perubahan password. Direktori temporer khusus proyek digunakan untuk tes ML karena direktori pytest Windows lama tidak dapat ditulis. Tidak ada klaim instalasi pada laptop teman sudah dijalankan.

Fixture Pendidikan yang dibuat ulang oleh tes browser sudah dihapus setelah tes. Verifikasi akhir memastikan tepat 25 pasangan kode/nama resmi, seluruhnya aktif, dan akun staf Pajak tidak ada.

README sekarang mencakup SQL pembuatan database/user, `.env`, instalasi dependensi, migrasi otomatis seluruh tabel, training ML, seed, tiga terminal backend/frontend/worker, akun demo, langkah upgrade/backup, pengujian dan troubleshooting. Tautan file lokal sudah diperiksa. Skenario dua dinas menggunakan Perizinan + Kesehatan sebagai simulasi.

Katalog tidak mengubah model menjadi 25 kelas. Model masih memiliki empat kelas lama; prediksi `pajak` masuk review karena tujuan sudah tidak tersedia. Pelatihan ulang untuk seluruh instansi adalah pekerjaan terpisah.
