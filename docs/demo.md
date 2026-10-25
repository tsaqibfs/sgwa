# Skenario demo dan penilaian

## Persiapan

Pastikan database, backend (8000), frontend (5173), migrasi, artefak model, dan akun seed tersedia. Siapkan tiga sesi/akun: warga, petugas Dukcapil, admin. Password awal berasal dari DEMO_PASSWORD lokal.

## Alur utama (sekitar 5 menit)

1. Buka beranda; jelaskan tujuan layanan publik dan bahwa ini prototipe akademik.
2. Login warga `warga@demo.sgwa.id`; buat permohonan:
   - Judul: Penggantian KTP yang hilang.
   - Deskripsi: Saya ingin mengurus KTP elektronik yang hilang dan kartu keluarga penduduk di Dukcapil. Mohon informasi dokumen yang perlu disiapkan.
3. Tunjukkan hasil klasifikasi, skor tiap dinas, versi model, dan status perlu review. Admin harus mengalihkan ke Dukcapil dengan catatan sebelum staf memproses.
4. Keluar, masuk `dukcapil@demo.sgwa.id`; buka permohonan dan klik Mulai proses.
5. Isi catatan dokumen lengkap; setujui melalui konfirmasi keputusan.
6. Login warga lagi; lihat hasil disetujui dan timeline keputusan.

## Eskalasi dan perluasan dinas (sekitar 3 menit)

1. Buat permohonan dengan teks tidak dikenal seperti `zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq`.
2. Sistem menandai perlu review, tanpa dinas tujuan yang dipaksakan.
3. Login admin; pilih DINAS PENDIDIKAN yang sudah ada pada katalog 25 instansi.
4. Isi alasan pengalihan dan reroute permohonan ke Pendidikan.
5. Tunjukkan bahwa riwayat prediksi lama tetap tersimpan dan dinas baru langsung menerima rute manual.
6. Jelaskan: klasifikasi otomatis ke dinas baru memerlukan data dan retraining; bukan sekadar menambah nama di admin.

## Penjelasan AI/ML (sekitar 2 menit)

Buka Evaluasi model. Jelaskan representasi TF-IDF, classifier Logistic Regression, split kelompok skenario, macro-F1, dan confusion matrix. Model25: macro-F1 holdout sintetis0,546; CV berbasis kelompok tersedia. Routing otomatis nonaktif karena validasi belum cukup; data nyata belum dibuktikan.

## Pertanyaan yang mungkin muncul

- **Di mana AI-nya?** Teks dikonversi menjadi fitur TF-IDF, kemudian classifier terlatih menghasilkan distribusi probabilitas kelas dinas.
- **Mengapa tidak chatbot?** Routing sesuai kebutuhan aplikasi dan bisa dilatih, diuji, serta dijelaskan tanpa biaya API.
- **Apakah AI memutuskan layanan?** Tidak. Staf/admin membuat keputusan final.
- **Bisa menambah dinas?** Bisa, melalui admin; kelas otomatis memerlukan training ulang.
- **Apa database-nya?** Oracle MySQL Community Server 9.7.2 di EnvKit, sudah diverifikasi langsung. Compose MySQL 8.4 juga tersedia.
- **Apa yang belum dibangun?** Laporan/CSV, analytics prediktif, coverage, CI, TLS/rate limiting, load test dan integrasi pemerintah nyata masih backlog.

## Demo tahap pertama: dua dinas, live, dan audit

1. Login admin, buka Aturan routing. Pilih Perizinan, centang DINAS KESEHATAN, simpan. Atur SLA dinas pada Dinas & layanan (1–90 hari kalender).
2. Login warga dan ajukan kebutuhan izin usaha. Model merekomendasikan kelas utama; admin mengalihkan ke Perizinan dan mencentang Kesehatan sebagai pendamping setelah review. Buka detail di satu jendela.
3. Di jendela terpisah login staf perizinan, mulai proses lalu setujui dengan catatan dan konfirmasi. Status keseluruhan masih Diproses.
4. Login staf kesehatan, mulai proses dan setujui. Status warga berubah langsung menjadi Disetujui tanpa refresh.
5. Admin membuka Jejak audit, filter aksi `request.task_updated`, lihat pelaku, waktu WIB, entitas dan perubahan.
6. Penolakan atau SLA lewat membuat permohonan masuk review admin; tugas dibekukan sampai keputusan final atau putaran routing baru. Riwayat putaran sebelumnya tetap terlihat.
7. Kembalikan aturan Perizinan ke dinas utama bila selesai demo.

Untuk menunjukkan SLA tanpa menunggu beberapa hari, gunakan pengujian `backend/tests/test_sla.py` pada schema test terpisah dengan waktu terkontrol. `python -m backend.app.sla.worker --once` menjalankan pemeriksaan nyata; jangan mengubah deadline data warga hanya untuk demo. SSE mempertahankan draft dan tersambung ulang otomatis; status koneksi tersedia di header.

## Demo fitur layanan tahap A

1. Semua role membuka Profil & keamanan. Ubah nama/telepon/alamat; untuk menunjukkan ganti password gunakan akun warga sintetis khusus, karena seluruh sesinya akan berakhir.
2. Admin membuka Formulir layanan, pilih instansi aktif, susun field, simpan draft lalu publikasikan. Warga dapat memilih layanan pada Pengajuan baru atau tetap mengirim judul/deskripsi tanpa formulir. Jika arah formulir berbeda dari kelas ML, permohonan masuk review admin.
3. Terbitkan versi berikutnya; detail permohonan sebelumnya tetap menampilkan label dan jawaban versi lama. Konflik publikasi meminta warga meninjau ulang jawaban sebelum mengirim kembali.
4. Buka Notifikasi: pengajuan, progres, pengalihan/eskalasi dan keputusan tersimpan. Tandai satu/semua dibaca, logout/login dan tunjukkan bahwa riwayat tetap ada.
5. Staf/admin membuka Simulasi pemeriksaan pada detail. Pilih identitas/kelengkapan izin/layanan umum dan skenario cocok/tidak cocok/tidak tersedia. Hasil memakai fixture sintetis dan tidak menyetujui layanan otomatis.
6. Setelah keputusan final, buka Lihat bukti hasil. Nomor, pemohon, waktu/catatan serta keputusan instansi merupakan snapshot. Gunakan Cetak / simpan PDF melalui browser; label demonstrasi akademik tetap tercetak. Bukti historis yang dikonversi menjelaskan informasi yang tidak tercatat.

Tidak ada riwayat/formulir contoh yang otomatis dimasukkan seed. Buat contoh secara sadar untuk demo; jangan memakai data pribadi asli.


## Pembaruan ML 25 kelas

Migrasi `0008`. Setup pertama: migrasi → seed → bootstrap → backfill. Startup ulang mempertahankan versi aktif. Gunakan [panduan ML](ml.md) untuk koreksi, verifikasi, training kandidat, aktivasi dan rollback. Pengajuan baseline saat ini memerlukan review manual admin; confidence minimal70% saja belum cukup untuk mengaktifkan routing otomatis.


## Laporan dan CSV — 13 Oktober 2026

Setelah backend dan frontend diperbarui, buka **Laporan layanan**. Scope mengikuti akun: warga miliknya, staf tugas dinasnya, admin seluruh permohonan. Tanggal pengajuan WIB (format query YYYY-MM-DD), status dan dinas diterapkan melalui **Terapkan filter**; CSV menggunakan filter applied dan seluruh halaman, maksimum5.000. Dinas pendamping ikut filter tetapi permohonan tidak diduplikasi.

Completion rate mencakup approved+rejected; durasi final memakai timestamp tersimpan; overdue hanya tugas dalam cakupan. File UTF-8 BOM, comma/CRLF dengan sanitasi formula dan tanpa kolom identitas/kontak/deskripsi/jawaban/catatan/feedback. Layar dan CSV merupakan snapshot masing-masing request; audit export_prepared hanya menyatakan file siap. Lihat [README](../README.md#laporan-layanan-dan-csv--13-oktober-2026) dan [verifikasi laporan](reports-verification.md).

Demo: buat permohonan pada schema E2E terpisah, admin alihkan ke dinas utama+pendamping, buka laporan warga lalu staf pendamping, terapkan filter dan unduh CSV. Admin melihat ringkasan lebih luas. Kasus lebih dari5.000 harus413; jangan membuat ribuan fixture pada database aplikasi hanya untuk demo. E2E laptop baru memakai .env.e2e dan scripts.prepare_e2e/run_e2e_server seperti panduan setup.
## Memahami keputusan admin dan dinas penanggung jawab

Pada permohonan yang perlu diperiksa admin, ada dua tindakan berbeda:

- **Alihkan permohonan:** pilih dinas utama, dinas pendamping bila diperlukan, dan catatan. Dinas yang ditetapkan akan tampil pada rincian permohonan warga dan menerima tugas untuk menindaklanjuti.
- Setelah dinas tujuan dipilih, tombol keputusan akhir langsung dinonaktifkan agar pilihan tersebut tidak terabaikan. Klik **Alihkan permohonan** untuk membuat tugas dinas. Kosongkan pilihan dinas jika ingin kembali ke keputusan akhir langsung.
- **Disetujui / Konfirmasi:** admin langsung menyelesaikan permohonan. Tindakan ini tidak menetapkan dinas baru. Jika belum pernah ada dinas yang ditetapkan, rincian warga menampilkan **Ditangani langsung oleh admin**, bukan **Menunggu pemeriksaan admin**. Penolakan langsung juga tidak berarti masih menunggu pemeriksaan.

Jangan memilih nama dinas berdasarkan dugaan sistem untuk mengisi riwayat permohonan yang sudah selesai. Gunakan dinas yang benar-benar ditetapkan pada proses pelayanan.

## Tampilan detail berdasarkan peran

Panel klasifikasi ML pada rincian permohonan hanya tampil untuk administrator. Warga dan staf dinas memakai tampilan satu kolom yang berfokus pada kebutuhan, penugasan, status, berkas dan hasil. Respons endpoint detail maupun perubahan permohonan mengembalikan `classification: null` untuk warga dan staf; admin tetap menerima prediksi historis. Pembatasan ini tidak menghapus hasil ML atau mengubah proses penentuan dinas. Laporan/CSV merupakan fitur terpisah dan tidak diubah oleh pembaruan tampilan detail ini.

Riwayat lama yang berbentuk `Dinas #1: processing` ditampilkan memakai nama dinas serta status bahasa Indonesia, misalnya `DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL: Diproses`. Jika nama dinas tidak tersedia, tampil keterangan `Petugas dinas`. Catatan asli di database tidak ditulis ulang; teks bebas petugas dipertahankan.
