# Skenario demo dan penilaian

## Persiapan

Pastikan database, backend (8000), frontend (5173), migrasi, artefak model, dan akun seed tersedia. Siapkan tiga sesi/akun: warga, petugas Dukcapil, admin. Password awal berasal dari DEMO_PASSWORD lokal.

## Alur utama (sekitar 5 menit)

1. Buka beranda; jelaskan tujuan layanan publik dan bahwa ini prototipe akademik.
2. Login warga `warga@demo.sgwa.id`; buat permohonan:
   - Judul: Penggantian KTP yang hilang.
   - Deskripsi: Saya ingin mengurus KTP elektronik yang hilang dan kartu keluarga penduduk di Dukcapil. Mohon informasi dokumen yang perlu disiapkan.
3. Tunjukkan hasil klasifikasi, skor tiap dinas, versi model, dan status menunggu.
4. Keluar, masuk `dukcapil@demo.sgwa.id`; buka permohonan dan klik Mulai proses.
5. Isi catatan dokumen lengkap; setujui melalui konfirmasi keputusan.
6. Login warga lagi; lihat hasil disetujui dan timeline keputusan.

## Eskalasi dan perluasan dinas (sekitar 3 menit)

1. Buat permohonan dengan teks tidak dikenal seperti `zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq`.
2. Sistem menandai perlu review, tanpa dinas tujuan yang dipaksakan.
3. Login admin; tambahkan Dinas Pendidikan dengan kode `pendidikan` jika belum ada.
4. Isi alasan pengalihan dan reroute permohonan ke Pendidikan.
5. Tunjukkan bahwa riwayat prediksi lama tetap tersimpan dan dinas baru langsung menerima rute manual.
6. Jelaskan: klasifikasi otomatis ke dinas baru memerlukan data dan retraining; bukan sekadar menambah nama di admin.

## Penjelasan AI/ML (sekitar 2 menit)

Buka Evaluasi model. Jelaskan representasi TF-IDF, classifier Logistic Regression, split kelompok skenario, macro-F1, dan confusion matrix. Hasil awal 1,000 hanya pada 40 contoh sintetis; bahasa bebas/typo/data nyata belum dibuktikan.

## Pertanyaan yang mungkin muncul

- **Di mana AI-nya?** Teks dikonversi menjadi fitur TF-IDF, kemudian classifier terlatih menghasilkan distribusi probabilitas kelas dinas.
- **Mengapa tidak chatbot?** Routing sesuai kebutuhan aplikasi dan bisa dilatih, diuji, serta dijelaskan tanpa biaya API.
- **Apakah AI memutuskan layanan?** Tidak. Staf/admin membuat keputusan final.
- **Bisa menambah dinas?** Bisa, melalui admin; kelas otomatis memerlukan training ulang.
- **Apa database-nya?** Kode memakai SQLAlchemy/PyMySQL untuk MySQL; sampaikan engine runtime yang benar-benar dipakai. Server EnvKit yang tersedia saat pengembangan adalah MariaDB 11.8.2; Oracle MySQL 8.4 disediakan sebagai konfigurasi Compose dan perlu diverifikasi bila diwajibkan.
- **Apa yang belum dibangun?** Orkestrasi multi-dinas paralel, integrasi pemerintah nyata, pembayaran, notifikasi eksternal, dan prediksi bottleneck.

## Demo tahap pertama: dua dinas, live, dan audit

1. Login admin, buka Aturan routing. Pilih Perizinan, centang Badan Pendapatan Daerah, simpan. Atur SLA dinas pada Dinas & layanan (1–90 hari kalender).
2. Login warga dan ajukan kebutuhan izin usaha. Model memilih kelas utama; aturan memperluasnya menjadi dua tugas. Buka detail di satu jendela.
3. Di jendela terpisah login staf perizinan, mulai proses lalu setujui dengan catatan dan konfirmasi. Status keseluruhan masih Diproses.
4. Login staf pajak, mulai proses dan setujui. Status warga berubah langsung menjadi Disetujui tanpa refresh.
5. Admin membuka Jejak audit, filter aksi `request.task_updated`, lihat pelaku, waktu WIB, entitas dan perubahan.
6. Penolakan atau SLA lewat membuat permohonan masuk review admin; tugas dibekukan sampai keputusan final atau putaran routing baru. Riwayat putaran sebelumnya tetap terlihat.
7. Kembalikan aturan Perizinan ke dinas utama bila selesai demo.

Untuk menunjukkan SLA tanpa menunggu beberapa hari, gunakan pengujian `backend/tests/test_sla.py` pada schema test terpisah dengan waktu terkontrol. `python -m backend.app.sla.worker --once` menjalankan pemeriksaan nyata; jangan mengubah deadline data warga hanya untuk demo. SSE mempertahankan draft dan tersambung ulang otomatis; status koneksi tersedia di header.
