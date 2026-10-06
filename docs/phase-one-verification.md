# Verifikasi tahap pertama — 6 Oktober 2026

Server EnvKit: `9.7.2`, `MySQL Community Server - GPL`, tabel InnoDB. Database aplikasi `sgwa_demo`, migrasi Alembic `0002`. Pengujian destruktif hanya pada `sgwa_test_codex`. Backup sebelum migrasi disimpan lokal di `.superpowers/backups/sgwa-demo-pre-phase-one-*.sql`, diabaikan Git.

Hasil: 45 tes backend/ML lulus, 9 tes unit frontend lulus, 8 tes browser Microsoft Edge lulus, TypeScript/Vite build berhasil. Pengujian mencakup migrasi data lama, routing dua dinas, versi/stale decision, penolakan dan review ulang, SLA/idempotensi worker, scope SSE, audit dan draft setelah sesi berakhir. Browser membuktikan perubahan staf muncul di akun warga tanpa refresh. Audit diperiksa pada 375, 768 dan 1366 px tanpa overflow halaman; tabel/nav dapat digeser. Tidak mengklaim load test atau kesiapan produksi.

Empat dummy `Dinas Pendidikan Demo` dengan kode `pendidikan_<timestamp>` beserta empat pengajuan fixture terkait telah dihapus melalui transaksi tervalidasi. Tidak ada dummy tersebut tersisa. Audit historis dipertahankan; pembersihan tercatat sebagai `demo.education_cleaned`. Script menolak data/staf di luar fixture yang dikenal. Tes browser berikutnya dapat menciptakan dummy lagi; jalankan `python -m scripts.cleanup_education_dummy` sesudah pengujian.

API, frontend dan worker SLA berjalan lokal. Pemeriksaan `--once` menghasilkan nol eskalasi karena tidak ada tugas aktif yang melewati tenggat. Worker memeriksa setiap 60 detik.

## Keputusan pelaksanaan

1. Memakai checkout feature yang sudah dipilih pengguna dan ledger Windows. Risiko: tidak ada isolasi tambahan terhadap perubahan lokal bersamaan.
2. Memakai Oracle MySQL 9.7.2 pilihan pengguna; 8.4 tetap referensi PRD/Compose. Risiko: bila penilaian mewajibkan versi persis 8.4, perlu menjalankan verifikasi di 8.4.
3. Mengunci katalog dinas menurut ID untuk konsistensi routing/penonaktifan. Risiko: throughput terbatas bila katalog dan trafik membesar.
4. Menerapkan migrasi sebelum tes UI agar API sesuai kontrak, setelah backup dan pengujian skema terpisah. Risiko: perubahan skema aplikasi lebih awal dari urutan rencana.

## Batas tahap pertama

AI tetap mengklasifikasikan satu kelas utama; aturan admin memperluas tujuan kerja. SLA berupa hari kalender, bukan kalender hari kerja. Semua tugas harus disetujui untuk persetujuan otomatis agregat. Penolakan atau SLA lewat memerlukan review admin; putaran baru menyimpan hasil lama dalam riwayat/audit.

Tahap 2/3 masih backlog: profil dan form builder, notifikasi persisten, laporan/CSV, sertifikat demo, mock API, cross-validation ML, CI, penguatan keamanan dan load test. Tidak ada integrasi pemerintah atau tanda tangan resmi. SSE membaca snapshot berkala; bukan jaminan notifikasi eksternal.

## Review akhir

Satu reviewer independen memeriksa keseluruhan tahap pertama. Tiga temuan penting diperbaiki melalui tes RED→GREEN: data detail dibersihkan saat 403/404, scope akun diverifikasi sebelum refresh setelah reconnect, dan tujuan routing nonaktif tetap dapat dihapus. Suite penuh setelah perbaikan: 45 backend, 9 unit frontend, 8 Edge; build berhasil. Tes worker sekarang benar-benar memotong antara candidate scan dan persetujuan terminal untuk membuktikan status final tidak ditimpa. Petunjuk demo yang usang juga diperbaiki. Tidak ada temuan minor yang ditunda.

Keputusan dari daftar yang tidak dinilai reviewer: tahap 2/3 tetap ditunda (fitur tersebut belum tersedia); kompatibilitas versi persis MySQL 8.4 belum diklaim (penilaian versi persis memerlukan tes terpisah); penguncian seluruh katalog diterima untuk demo (risiko contention pada trafik besar).
