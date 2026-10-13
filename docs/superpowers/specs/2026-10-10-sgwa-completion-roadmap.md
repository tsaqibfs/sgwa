# Roadmap penyelesaian SGWA

Tanggal: 10 Oktober 2026. Status: usulan untuk review, belum merupakan hasil implementasi.

## Tujuan dan keputusan pengguna

Proyek akhir semester untuk demo dan penilaian. MySQL tetap menjadi database aplikasi; backend Python dan frontend React yang ada dipertahankan. Fokus terbaru pengguna adalah profil/ganti password, form builder, notifikasi persisten, bukti hasil, mock API, laporan/CSV, analytics prediktif, cross-validation, coverage, CI, TLS/rate limiting, load test, serta training ulang menjadi 25 kelas ML.

Pengguna memastikan belum ada dataset nyata dan memilih **data sintetis untuk demo dengan label sumber data yang jelas**. Lima akun seed saat ini tetap untuk demo; penambahan 25 kelas tidak otomatis membuat 25 akun staf atau mengubah ID instansi yang ada.

Baseline: workflow paralel, SLA, SSE, audit, routing admin, katalog 25 instansi dan paket Docker telah tersedia. Model saat ini masih empat kelas. Dokumen lama menyebut katalog/Pajak dan engine historis; roadmap ini memakai katalog terbaru dan Oracle MySQL yang sekarang digunakan.

## Pilihan pendekatan

1. **Bertahap di aplikasi yang ada — direkomendasikan.** Selesaikan fitur layanan, kemudian ML/pelaporan, kemudian kualitas deployment. Tiap tahap memiliki migrasi, pengujian, dokumentasi, dan kriteria selesai sendiri. Demo tetap dapat dijalankan setelah setiap tahap.
2. Semua subsistem sekaligus. Integrasi bisa dilakukan dalam satu rangkaian besar, tetapi diagnosis kegagalan dan review lebih sulit karena banyak kontrak berubah bersamaan.
3. Dahulukan ML 25 kelas. Memperluas demonstrasi AI lebih cepat, tetapi profil, formulir dan layanan pengguna tetap belum lengkap. Pilihan ini masuk akal jika penilaian dosen terutama pada ML; belum ada informasi yang mengharuskan urutan tersebut.

Urutan yang diusulkan adalah pilihan pertama. Semua item tetap tercakup; pembagian tahap bukan menghapus scope.

## Tahap A — fitur layanan

Spesifikasi terpisah: [rancangan fitur layanan](2026-10-10-sgwa-service-features-design.md).

Hasil demo: warga mengubah profil/password, mengisi formulir layanan, menerima notifikasi tersimpan, dan mencetak bukti keputusan; staf melihat hasil pemeriksaan mock yang jelas sebagai simulasi. Admin mengelola formulir dan publikasinya. Semua perubahan mempertahankan audit, kontrol akses dan transaksi workflow.

## Tahap B — ML 25 kelas, laporan dan analytics

- Label dataset harus persis 25 kode pada `backend/app/agencies/catalog.py`; label Pajak lama tidak dipakai dalam training baru. Artefak prediksi historis tidak ditulis ulang.
- Target awal dataset sintetis adalah 100 contoh per kelas, total 2.500, dengan sedikitnya 10 keluarga skenario independen per kelas. Ini target desain dataset, bukan bukti keragaman bahasa dunia nyata. Variasi dari satu template harus berbagi group_id. Dataset dan generator diberi versi; seed acak tetap agar dapat direproduksi.
- Pisahkan kelompok holdout sebelum training. Jalankan cross-validation berstrata berbasis kelompok pada bagian training saja, dengan TF-IDF dilatih ulang di setiap fold. Variasi satu keluarga tidak boleh melintasi train/validation/test. Hasil holdout tidak dipakai memilih hyperparameter.
- Laporkan macro-F1, precision/recall/F1 setiap kelas, confusion matrix 25 kelas, rata-rata dan variasi skor fold, jumlah contoh/kelompok, seed dan hash dataset/model. Jelaskan kelas yang sulit dibedakan seperti pertanian/peternakan/perikanan atau pekerjaan umum/perumahan.
- UI evaluasi, ekspor dan README menampilkan bahwa data sintetis, sehingga skor tinggi tidak diklaim sebagai akurasi permohonan warga nyata. Uji teks tak dikenal, ambigu dan confidence rendah; fallback review manusia tetap berlaku. Ambang confidence harus dipilih dari validasi, bukan dari holdout.
- Ekspor CSV mengikuti scope role: warga hanya miliknya, staf hanya tugas dinasnya, admin semua dengan filter waktu/status/dinas. Lindungi CSV formula injection dan uji encoding, escaping, pagination serta batas ekspor.
- Analytics prediktif pertama memprediksi volume permohonan harian per dinas, dengan baseline sederhana dan evaluasi berdasarkan urutan waktu. Minimum riwayat 60 hari diperlukan untuk mengaktifkan forecast; ketika kurang, tampilkan "data belum cukup". Data riwayat sintetis untuk demonstrasi dipisahkan dari data aplikasi dan diberi label simulasi, tidak disisipkan sebagai riwayat nyata. Grafik deskriptif tetap tersedia tanpa forecast.
- Training Docker diperbarui agar menghasilkan model baru; metadata memvalidasi kesesuaian seluruh 25 label. Pergantian model dan restart API/worker didokumentasikan, termasuk penyimpanan artefak sebelumnya untuk rollback.
- Tambahkan pembelajaran berbasis feedback yang telah dibahas dan disetujui untuk dilanjutkan: admin secara eksplisit mengoreksi kelas utama, bukan sekadar menambah dinas workflow. Simpan teks, prediksi/versi model, label koreksi, pemeriksa, waktu dan provenance sintetis/nyata di MySQL. Koreksi diverifikasi sebelum diekspor sebagai data training; prediksi sendiri tidak menjadi ground truth. Training ulang batch menghasilkan kandidat versi baru yang dievaluasi sebelum aktivasi, dengan artefak versi sebelumnya untuk rollback. Holdout tetap terpisah, dan feedback duplikat/variasi keluarga yang sama tetap dikelompokkan. Tidak ada perubahan bobot online pada setiap permohonan atau klaim peningkatan otomatis.

Detail kontrak dataset, forecast, API ekspor dan aktivasi model akan ditulis pada spec tahap B setelah tahap A, sebelum implementasi tahap B.

## Tahap C — bukti kualitas dan deployment

- Coverage dijalankan pada suite MySQL terisolasi dan ML, dengan laporan terminal/XML/HTML. Ambang proyek usulan 80% statement coverage untuk backend dan ML, disertai daftar modul belum tercakup; bukan klaim syarat PRD atau hasil yang sudah tercapai. Tes otorisasi, transaksi, concurrency dan kegagalan lebih penting daripada mengejar angka dengan tes yang meniru kode.
- CI membangun frontend, menjalankan backend/ML dengan MySQL 8.4, migrasi database baru, coverage dan smoke Docker. Secret CI terpisah dari laptop, tidak menyalin `.env`; gunakan akun DB khusus schema pengujian. Target layanan CI adalah GitHub Actions apabila repository akan dihost di GitHub. Hosting repository belum diasumsikan sudah tersedia.
- TLS berupa opsi deployment Compose terpisah dengan reverse proxy HTTPS. Untuk demo lokal tersedia sertifikat lokal; sertifikat publik memerlukan domain yang dikuasai pengguna. Cookie Secure dan trusted origins harus mengikuti HTTPS. Jangan mengganti akses HTTP demo sebelum jalur HTTPS diuji.
- Rate limiting dipasang untuk login/register dan mutasi API, dengan 429 dan Retry-After. Konfigurasi awal satu proses API sesuai demo; jika beberapa replika diperlukan, limiter harus memakai penyimpanan bersama MySQL. IP forwarding hanya dipercaya dari proxy yang dikonfigurasi. Endpoint SSE perlu batas koneksi per akun dan tidak memakai bucket frekuensi polling HTTP.
- Load test memakai lingkungan/schema khusus, bukan data EnvKit atau container demo. Ukur login, daftar/detail, submit, keputusan workflow dan koneksi SSE pada tingkat concurrency yang dinyatakan. Simpan p50/p95/p99, throughput, error rate, resource mesin dan durasi. Target usulan smoke beban adalah 20 pengguna bersamaan selama 5 menit, error tak terduga <1%, p95 request HTTP biasa <1 detik pada mesin uji; bukan jaminan kapasitas produksi. Konflik version 409 yang sengaja diuji dilaporkan terpisah.

Detail TLS/limiter/load test dan target CI diselesaikan pada spec tahap C berdasarkan deployment setelah tahap A/B.

## Integrasi dan selesai

Tidak ada reset database otomatis. Perubahan skema memakai Alembic dan diuji pada database kosong serta salinan database versi sebelumnya. Native/EnvKit dan Docker tetap punya environment serta volume terpisah. Seed tidak membuat permohonan demo massal. Setiap tahap memperbarui README, skenario demo, status PRD dan laporan verifikasi sesuai hasil aktual.

Seluruh scope baru dianggap selesai setelah ketiga tahap lolos verifikasi dan keterbatasan sintetis tercantum pada produk/laporan. Roadmap atau spec yang disetujui bukan bukti fitur sudah tersedia.


## Status implementasi — 11 Oktober 2026

Tahap A tersedia. Bagian ML tahap B tersedia:25 kelas, cross-validation, normalisasi, feedback terverifikasi, kandidat batch, aktivasi/rollback dan bootstrap aman. Holdout sintetis macro-F1 0,546; routing otomatis nonaktif. Laporan/CSV dan analytics prediktif tahap B, serta tahap C, masih backlog. Lihat docs/ml-feedback-verification.md untuk bukti terbaru; uraian baseline di atas adalah konteks rancangan historis.


## Status tahap laporan — 13 Oktober 2026

Laporan/CSV tahap B telah diimplementasikan: scope role, filter tanggal WIB/status/dinas termasuk pendamping, summary/page, CSV lengkap sampai5.000, formula safety, audit metadata dan snapshot RR. Tanpa migrasi/model training. Analytics prediktif tahap B dan seluruh tahap C masih backlog. Kualitas ML baseline/normalizer/pointer tidak diubah; lihat docs/reports-verification.md untuk bukti terbaru.
