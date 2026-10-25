# Verifikasi tampilan detail dan pembatasan klasifikasi ML

Tanggal: 24 Oktober 2026.

## Perubahan

- Panel klasifikasi ML pada detail permohonan hanya ditampilkan untuk admin. Warga/staf memakai satu kolom tanpa ruang kosong panel.
- Semua endpoint detail dan perubahan permohonan mengembalikan `classification: null` kepada warga/staf. Admin tetap menerima snapshot prediksi, dan data historis ML tetap tersimpan. Perubahan ini tidak mengubah laporan/CSV yang merupakan fitur terpisah.
- Prefix sistem seperti `Dinas #1: processing.` ditampilkan dengan nama dinas dan status bahasa Indonesia. Teks asli di database dan isi bebas catatan petugas tidak ditulis ulang.
- Regresi menemukan kesalahan lama pada riwayat unggah/hapus lampiran: `to_status` kosong melanggar constraint database. Event lampiran kini mencatat status permohonan saat itu tanpa mengubah status pelayanan. Tes memakai direktori file sementara dan prediksi deterministik agar cakupan staf tidak bergantung pada skor model.
- Dua tes upgrade disesuaikan dengan migrasi terbaru `0009` dan keberadaan tabel lampiran; tidak ada migrasi baru dalam perubahan tampilan ini.

## Bukti pengujian

- Frontend RED: 5 gagal/9 lulus; gagal karena panel terlihat untuk warga/staf dan riwayat masih memakai prefix teknis. Setelah perubahan: 14 tes terarah lulus.
- Backend RED: 2 tes izin gagal sebelum proyeksi menurut peran diterapkan; keduanya lulus setelah perubahan. Mencakup submit, detail, keputusan staf, review-route, reroute, keputusan admin, serta penyimpanan prediksi historis.
- Regresi frontend: 44 lulus, 18,35 detik. Build TypeScript/Vite lulus, 11,35 detik.
- Edge: 3 lulus, 10,9 detik. Ketiga peran diperiksa pada 375/768/1366 piksel, tanpa overflow horizontal. Tes ini memakai respons API simulasi untuk mengisolasi pemeriksaan tampilan; bukan bukti usability responden atau pengujian kewenangan server.
- Run backend/ML penuh awal: 127 lulus, 3 gagal, 592,21 detik. Kegagalan terdiri dari satu kasus lampiran dan dua ekspektasi migrasi lama.
- Setelah perbaikan, run terkait endpoint/penugasan/riwayat/migrasi: 29 lulus, 1 gagal karena isolasi direktori upload pada fixture tes belum mencakup jalur download.
- Setelah fixture diperbaiki melalui konfigurasi direktori bersama, lima tes yang mencakup lampiran, izin klasifikasi dan upgrade migrasi lulus seluruhnya, 69,57 detik. Run penuh 130 tes tidak diulang; angka run awal tidak dinyatakan sebagai hasil penuh yang lulus.
- Pemeriksaan HTTP pada backend native memverifikasi akun demo admin, staf Dukcapil dan warga: endpoint detail dapat diakses sesuai scope; rincian ML hanya diterima admin.

## Batas dan penggunaan

Pengujian database menggunakan MySQL khusus tes di port 3308, terpisah dari EnvKit. Backend lokal port 8000 dimuat ulang; frontend pengembangan port 5173 menyajikan perubahan. Worker SLA tidak dihentikan. Container aplikasi Docker tidak dibangun ulang dalam perubahan ini.

Tes browser ML yang melatih/mengaktifkan model diperbarui agar pemeriksaan versi prediksi dilakukan melalui admin; suite browser yang mengubah model tersebut tidak dijalankan pada database aplikasi. Bukti di atas merupakan verifikasi perangkat lunak, bukan hasil eksperimen routing independen atau data usability pengguna.
