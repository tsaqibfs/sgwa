# ML 25 kelas dan pembelajaran dari koreksi admin

Tanggal: 10 Oktober 2026. Status: rancangan untuk review pengguna; belum diimplementasikan.

## Tujuan dan batas tahap

SGWA adalah proyek akhir semester untuk demonstrasi dan penilaian. Pengguna meminta melanjutkan ML 25 kelas dan alur koreksi admin, serta sebelumnya memilih data sintetis karena belum memiliki dataset nyata. Pertahankan backend Python, frontend React, MySQL, 25 instansi resmi, workflow dan riwayat yang sudah ada.

Tahap ini menghasilkan model lokal 25 kelas, evaluasi yang dapat direproduksi, koreksi berlabel yang diverifikasi admin, training batch kandidat, aktivasi dan rollback melalui admin. Keberhasilan tidak berarti skor harus meningkat atau model mampu menggeneralisasi ke warga nyata. Model tidak memutuskan persetujuan layanan.

Laporan layanan/CSV umum, forecast volume, coverage/CI, TLS/rate limiting, load test dan phpMyAdmin berada di luar tahap ini. Ekspor internal feedback untuk training termasuk tahap ini.

## Pilihan dan rekomendasi

1. **Batch training dan aktivasi manual — dipilih sebagai rekomendasi.** Koreksi diverifikasi, training dijalankan lewat CLI, kandidat dievaluasi, admin mengaktifkan versi yang lolos syarat. Cocok untuk demo, dapat diaudit, dan tidak memerlukan antrean pekerjaan training baru.
2. Training terjadwal otomatis dengan aktivasi manual. Dapat ditambahkan ketika data cukup, tetapi scheduler dan kebijakan interval belum diperlukan pada tahap ini.
3. Pembaruan bobot pada setiap koreksi. Tidak dipilih: TF-IDF/Logistic Regression saat ini memakai batch fit dan perubahan langsung menyulitkan validasi serta rollback.

Training dimulai melalui perintah operator yang didokumentasikan, termasuk `docker compose run --rm ...`; UI menjelaskan langkah tersebut. Tombol aktivasi/rollback tersedia di web. Antrean training dari web tidak termasuk tahap ini.

## Dataset 25 kelas

- Kode label persis 25 kode `backend/app/agencies/catalog.py::AGENCIES`. Label `pajak` tidak digunakan dalam dataset baru. Menambah instansi lain tetap memerlukan dataset dan training baru.
- Generator deterministik menghasilkan minimal 100 contoh per kelas: minimal 10 keluarga skenario per kelas dan 10 variasi per keluarga, total minimal 2.500 contoh. Skenario harus dibedakan berdasarkan kebutuhan layanan, bukan hanya perubahan kata pembuka.
- Variasi dari keluarga sama memakai `group_id` yang sama. Simpan `text`, `label`, `group_id`, `provenance=synthetic`, `dataset_version` dan hash teks ternormalisasi. Generator dan keluarga skenario diberi versi. Tidak menambahkan permohonan sintetis massal ke database aplikasi.
- Sertakan layanan yang berdekatan: pangan/pertanian vs peternakan vs perikanan; bina marga vs sumber daya air vs perumahan/cipta karya; perizinan vs perindustrian/perdagangan vs koperasi; dukcapil vs pengendalian penduduk/KB. Teks ambigu tidak dipaksakan menjadi contoh satu kelas yang jelas.
- Pisahkan 20% kelompok per kelas sebagai holdout tetap sebelum training. Manifest holdout disimpan dan diberi hash; retraining berikutnya wajib memakai holdout yang sama. Perubahan dataset utama menghasilkan generasi evaluasi baru dan tidak dapat dibandingkan seolah memakai holdout lama.
- Duplikat teks ternormalisasi tidak boleh melintasi split. Generator, importer dan training memvalidasi duplikat, konflik label dan kelompok. Konflik membatalkan training dengan pesan yang dapat ditindaklanjuti.

## Training, cross-validation dan confidence

- Pertahankan pipeline TF-IDF unigram/bigram dan Logistic Regression; parameter dasar `C=4`, `max_iter=1000`, seed 42. Tidak perlu pencarian hyperparameter besar pada tahap ini.
- Jalankan 5-fold stratified group cross-validation hanya pada bagian non-holdout. TF-IDF selalu di-fit ulang pada training setiap fold. Setiap kelas harus memiliki cukup kelompok untuk seluruh fold; kekurangan kelompok merupakan error, bukan fallback ke random row split.
- Pilih threshold dari prediksi out-of-fold, bukan holdout. Uji grid 0,40 sampai 0,95 dengan langkah 0,05. Pilih threshold dengan coverage terbesar yang memiliki precision prediksi yang diterima minimal 0,90 dan minimal 25 contoh diterima. Bila tidak ada yang memenuhi, tandai routing otomatis nonaktif; semua pengajuan masuk review manusia.
- Laporkan coverage dan precision accepted, sehingga threshold tinggi dengan sedikit keputusan tidak disajikan sebagai keberhasilan keseluruhan. Angka precision pada data sintetis bukan jaminan precision pada data nyata.
- Fit model final pada seluruh bagian non-holdout, lalu evaluasi holdout sekali untuk laporan. Simpan skor setiap fold, mean/std macro-F1, per-class precision/recall/F1, confusion matrix 25x25, kesalahan, jumlah contoh/kelompok tiap split, provenance counts, seed, parameter, versi dataset, hash dataset/model dan manifest holdout.
- `submit_request` memakai threshold dan flag auto-routing dari metadata model yang benar-benar dipakai untuk prediksi, menggantikan konstanta 0,60. Tidak ada fitur dikenal, confidence rendah, instansi nonaktif, route tidak valid atau ketidakcocokan instansi formulir tetap masuk review admin.
- Uji teks asing/tidak dikenal, typo, ambigu dan layanan berdekatan. Tidak menjanjikan seluruh teks ambigu akan terdeteksi; confidence classifier ini belum dikalibrasi untuk populasi nyata.

## Koreksi dan verifikasi admin

- Koreksi ML berbeda dari pengalihan workflow. Menambah dinas pendamping atau mengalihkan permohonan tidak otomatis menjadi label training.
- Admin membuka detail permohonan, melihat prediksi awal/versi model, memilih satu kelas utama dari katalog aktif, mengisi alasan dan memilih provenance secara eksplisit: `synthetic_demo` atau `real`. Akun demo tidak membuktikan teks berasal dari warga nyata.
- Provenance wajib dipilih dan tidak diturunkan otomatis dari email. Form mengingatkan bahwa teks training tidak boleh memuat data pribadi; admin mengisi teks training yang sudah disunting. UI memperlihatkan teks asli hanya dalam detail permohonan yang sudah berizin.
- Teks asli prediksi, label/probabilitas/model awal, teks training tersunting, hash normalisasi, kelas koreksi, provenance, alasan, penulis/waktu disimpan sebagai snapshot MySQL. Payload client tidak boleh memalsukan snapshot prediksi atau identitas penulis.
- Status awal `pending`; admin memverifikasi menjadi `verified` atau menolak `rejected` dengan catatan. Satu admin boleh melakukan keduanya untuk demo dan identitas aktor selalu tercatat. Ini verifikasi manusia, bukan adjudikasi independen oleh dua petugas.
- Revisi menggantikan feedback sebelumnya sebagai `superseded` dan menghasilkan revision baru. Simpan histori immutable. Gunakan nomor revision/current pointer dan expected revision untuk konflik 409. Retry dengan idempotency key yang sama tidak membuat duplikat; payload berbeda pada key sama ditolak.
- Semua mutasi admin-only, dilindungi cookie/CSRF dan audit dalam transaksi yang sama. Warga/staf tidak dapat melihat dataset feedback atau melakukan verifikasi.
- Koreksi dapat dicatat pada permohonan yang sudah selesai karena hanya memperbaiki data training; status workflow, hasil layanan, notifikasi dan prediksi awal tidak berubah.

## Snapshot feedback untuk training

- Exporter internal membaca hanya feedback current, verified, dan 25 label yang valid. Ambil snapshot konsisten dalam transaksi; manifest mencatat ID/revision feedback dan hash snapshot. Training di luar transaksi tersebut.
- Duplikat teks tersunting dikelompokkan berdasarkan hash. Label yang berbeda untuk teks sama membatalkan ekspor, dengan ID yang perlu diperiksa. Contoh yang tumpang tindih dataset dasar diberi kelompok dasar yang sama; contoh yang tumpang tindih holdout dikeluarkan dan dilaporkan.
- Kelompokkan semua feedback dari permohonan yang sama dan duplikat persis. Kemiripan semantik tidak dideteksi otomatis pada tahap ini: admin dapat memberi family key agar parafrasa sekeluarga tetap satu group. Bila family key diberi, gunakan namespace feedback; konflik/label berbeda ditolak. Dokumentasikan bahwa parafrasa tanpa family key masih berpotensi bocor.
- Feedback menambah dataset non-holdout, tidak pernah menambah holdout. Tidak ada training langsung dari prediksi model sendiri, status approved, atau reroute workflow.
- Artefak campuran menyebut jumlah data sintetis dan nyata secara terpisah. Evaluasi holdout tetap diberi label **holdout sintetis**, termasuk ketika training memakai feedback nyata.
- Feedback yang sudah digunakan tetap tersimpan. Training ulang dengan snapshot sama menghasilkan identitas konten yang sama dan tidak menggandakan baris training.

## Versi model, aktivasi dan rollback

- Artefak disimpan dalam `MODEL_DIR/versions/<generated-id>/`; ID dihasilkan server/CLI, tidak berasal dari path pengguna. Tiap direktori immutable berisi model, metadata, evaluasi, split CSV dan manifest. Identitas versi mencakup data, parameter, manifest holdout dan format training; tidak hanya hash dataset.
- Training CLI membuat direktori staging, menulis artefak, memvalidasi hash dan kelas, lalu mempublikasikan direktori final. Tidak menimpa model aktif. Model menggunakan joblib dari training lokal terpercaya; tidak ada upload artefak lewat web.
- Registry MySQL menyimpan versi, status kandidat/siap/gagal, lokasi relatif yang divalidasi, hash, report summary, waktu/aktor registrasi dan hubungan dataset/feedback snapshot. Tabel singleton menyimpan pointer model aktif dengan revision untuk optimistic concurrency.
- Kandidat wajib tepat 25 kelas, seluruh artefak valid, CV lengkap dan holdout sebanding. Untuk kandidat pertama, semua persyaratan teknis harus lolos; target macro-F1 0,85 bersifat target yang dilaporkan, bukan angka yang dipalsukan. Admin melihat peringatan bila di bawah target.
- Untuk kandidat berikutnya, holdout macro-F1 tidak boleh turun lebih dari 0,02 dari model aktif pada manifest holdout yang sama. Per-class recall dan perubahan threshold/coverage tetap ditampilkan untuk penilaian admin. Kandidat gagal gate tidak dapat diaktifkan lewat UI/API; tidak ada override tersembunyi.
- Aktivasi manual memerlukan expected pointer revision dan alasan; validasi artefak sebelum mengubah pointer. Riwayat aktivasi dan rollback dicatat. Rollback memilih versi yang pernah aktif dalam generasi 25 kelas ini dan masih valid; tidak otomatis kembali ke model lama 4 kelas.
- Backend membaca pointer aktif untuk inferensi dan metadata/evaluation, memuat serta cache classifier immutable per versi, dan gagal aman jika file aktif rusak/tidak tersedia (503 untuk inferensi, pesan admin). Tidak diam-diam menggunakan cache versi lama saat pointer menunjuk versi baru yang gagal dimuat.
- Tiap prediksi mengambil satu snapshot classifier dan metadata sampai transaksi submit selesai. Aktivasi bersamaan tidak mencampur probabilitas versi lama dengan threshold versi baru. Histori request dan classification tidak ditulis ulang.
- Pointer berbasis MySQL membuat native dan Docker konsisten dalam lingkungan masing-masing tanpa bergantung restart untuk aktivasi. Kedua database dan direktori artefak tetap terpisah.

## Bootstrap dan kompatibilitas

- Migrasi additive setelah `0007`; tidak mereset data atau mengubah ID instansi. Backup EnvKit sebelum migrasi dan uji pada database kosong serta salinan versi sebelumnya.
- Artefak empat kelas lama diarsipkan sebelum bootstrap pertama. Karena registrasi 25 kelas belum ada, fase perpindahan dilakukan secara eksplisit oleh operator sebelum backend dijalankan kembali. Histori `model_version` lama tetap valid sebagai snapshot.
- Bootstrap membangun dataset dasar, training kandidat 25 kelas, mendaftarkannya dan mengaktifkan versi pertama setelah verifikasi teknis. Ini langkah pemasangan yang terlihat di log, berbeda dari retraining feedback yang selalu kandidat dan butuh aktivasi admin.
- Startup Docker berikutnya menjalankan migrasi dan seed, memvalidasi pointer aktif dan artefak, serta mempertahankan pilihan admin. Tidak melatih/menimpa/aktifkan model baru setiap `up --build`. Model volume dibagi dengan CLI training; backend hanya perlu akses baca artefak.
- Bila registry aktif ada tetapi artefak hilang, startup memberikan error yang jelas; tidak menganggapnya instalasi baru. Dokumen menyediakan recovery/rollback dan perintah native/Docker.

## Antarmuka

- Detail permohonan admin: panel terpisah “Koreksi klasifikasi untuk training”, provenance, teks tersunting, label/alasan, riwayat revision dan verifikasi. Penyimpanan tidak memanggil endpoint reroute.
- Halaman model: 25 nama instansi, informasi sintetis, fold mean/std, holdout, threshold/coverage, confusion matrix yang dapat digulir, dan daftar kandidat/aktif dengan aktivasi atau rollback. Nama dan angka berasal dari API, bukan hardcoded.
- Halaman feedback admin: daftar terpaginasikan dengan status/provenance dan detail, aksi verifikasi/tolak, serta petunjuk perintah training. Jangan tampilkan job sukses bila operator belum benar-benar menjalankan training.
- Tampilkan error/409 dan muat ulang data sebelum mengulang aksi. Respons training gagal disimpan/dicatat oleh CLI; UI tidak menampilkan kandidat gagal sebagai siap.
- Gunakan komponen dan gaya aplikasi yang sudah ada; layout 375/768/1366 px tetap dapat dipakai. Tidak melakukan redesign umum.

## Kriteria verifikasi

1. Dataset deterministik, tepat 25 label, minimal 2.500 baris/250 keluarga, tiada pajak, hash/manifest reproducible dan tidak ada kebocoran kelompok atau teks persis.
2. CV hanya non-holdout; vectorizer di-fit per fold; threshold dari out-of-fold; seluruh laporan 25 kelas dan provenance benar. Repeated train konsisten dalam environment yang sama.
3. Admin-only dan CSRF, snapshot server-side, verifikasi/revisi, idempotency, konflik concurrent, audit rollback dan workflow/result/prediksi awal tidak berubah.
4. Snapshot feedback hanya current verified, duplicate conflicts, family groups, holdout overlap, data sintetis/nyata dan daftar exclusion dibuktikan oleh tes.
5. Registrasi parsial/artefak rusak tidak menjadi aktif; activation/rollback concurrent memiliki satu pointer; inferensi memakai versi/threshold yang sama; stale cache tidak menyamarkan kegagalan model aktif.
6. Migration upgrade database kosong dan database `0007` berisi data mempertahankan row/kolom lama. Tidak menyuntikkan permohonan dataset ke aplikasi.
7. Browser membuktikan koreksi → verifikasi → daftar kandidat hasil CLI → aktivasi → permohonan baru memakai versi baru; permohonan lama tetap memakai versi lama. Uji role dan layout.
8. Native EnvKit dan Docker diuji terpisah, mencatat model aktif, 25 kelas, startup kedua yang mempertahankan model, serta kegagalan dan rollback. Tes mutasi/beban memakai database terisolasi.
9. README, docs/ml.md, Docker/setup/demo dan catatan verifikasi mengikuti hasil aktual, termasuk keterbatasan data sintetis dan perintah retraining.

## Self-review rancangan

Ruang lingkup dipersempit dari tahap B roadmap menjadi ML dan feedback. Training lewat CLI menghindari job queue baru; web menangani review/aktivasi. Dataset dan feedback memakai kelompok eksplisit, holdout immutable, identitas konten dan provenance terpisah. Tidak ada klaim model otomatis lebih baik, online learning, atau skor sintetik sebagai akurasi warga nyata. Kontrak API/tabel/rangkaian tes diperinci dalam implementation plan setelah rancangan ini direview pengguna.
