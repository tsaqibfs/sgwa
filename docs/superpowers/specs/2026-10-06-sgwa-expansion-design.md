# Perluasan SGWA berdasarkan PRD

Tanggal: 6 Oktober 2026. Status: rancangan untuk ditinjau; belum diimplementasikan.

## Tujuan dan batas

Pengguna meminta penambahan kebutuhan PRD yang masih kurang pada web proyek akhir semester. Fondasi FastAPI, React, ML lokal, dan tampilan yang telah disetujui dipertahankan. Database tetap MySQL sesuai ketentuan pengguna. Tidak ada integrasi pemerintah produksi, pembayaran, atau tanda tangan elektronik tersertifikasi karena PRD mengecualikannya.

Keberhasilan: demo memperlihatkan satu pengajuan melibatkan beberapa dinas, keputusan tiap dinas, eskalasi dan pemeriksaan manusia, tenggat SLA, perubahan status otomatis di layar, serta audit yang dapat ditelusuri. Fitur tambahan dan bukti kualitas diselesaikan dalam tahap berikutnya, bukan dianggap sudah lengkap setelah tahap pertama.

## Engine database

Pemeriksaan koneksi DATABASE_URL pada 6 Oktober 2026 mengembalikan VERSION() = `11.8.2-MariaDB`, @@version_comment = `mariadb.org binary distribution`. Pernyataan ini hanya mengidentifikasi koneksi aplikasi saat pemeriksaan, bukan seluruh layanan yang mungkin tersedia dalam EnvKit. Konfigurasi driver `mysql+pymysql` tidak menentukan produk server.

Tidak menimpa database lama atau menghapus layanan EnvKit. Inspeksi konfigurasi layanan dapat menemukan Oracle MySQL yang tersedia; jika tidak ada, lingkungan Oracle MySQL terpisah diperlukan untuk verifikasi. Migrasi dan suite harus dijalankan di Oracle MySQL sebelum persyaratan engine dinyatakan terpenuhi. Kredensial tetap berada di .env dan tidak dicetak. Pengembangan dengan koneksi yang ada boleh berlanjut dengan keterbatasan yang dicatat.

## Tahap 1: workflow paralel, SLA, pembaruan langsung, audit

### Model dan migrasi

Tambahkan `request_workflows`: request_id, agency_id, status, version, due_at, completed_at, decision_note, created_at, updated_at. Kombinasi request/dinas unik. Status tugas dinas: pending, processing, approved, rejected. Permohonan tetap memiliki status agregat dan version tersendiri. Tambahkan agency.sla_days (integer 1–90, default 3 hari kalender) dan konfigurasi rute kelas ML ke satu atau beberapa dinas aktif.

Migrasi mempertahankan pengajuan lama, classification_results, timeline dan audit. Pengajuan lama yang memiliki dinas dijadikan satu tugas dinas dengan status dan waktu yang sesuai; kasus escalated tetap memerlukan review tanpa dibuat seolah memiliki SLA lama. Due_at pengajuan lama yang masih terbuka dihitung dari waktu migrasi untuk menghindari eskalasi massal. assigned_agency_id dipertahankan sementara sebagai dinas utama agar interface lama dapat diadaptasi bertahap. Konfigurasi rute awal satu kelas ke dinas yang sama.

### Routing dan keputusan

Classifier tetap memprediksi satu kelas utama. Aturan workflow yang dikonfigurasi admin memperluas kelas tersebut menjadi dinas yang perlu memproses bersama. Jangan mengklaim classifier telah menjadi model multi-label. Admin dapat mengatur contoh rute Perizinan → Perizinan + Pajak. Dinas nonaktif tidak menerima tugas baru; rute tidak valid masuk review. Confidence rendah atau teks tidak dikenal tetap escalated tanpa routing otomatis.

Staf melihat pengajuan jika terdapat tugas untuk dinasnya, lalu hanya mengubah tugas dinas tersebut. pending → processing → approved/rejected. Keputusan dan eskalasi harus disertai alasan. Permohonan menjadi processing ketika tugas mulai dikerjakan; approved hanya setelah seluruh dinas menyetujui. Penolakan satu dinas atau eskalasi manual menyebabkan permohonan escalated, bukan langsung rejected. Saat escalated, tugas dibekukan untuk menunggu pemeriksaan admin. Admin dapat menetapkan approved/rejected dengan alasan atau menetapkan ulang daftar dinas untuk review baru; keputusan putaran lama disimpan pada timeline sebelum tugas direset. Keputusan admin dicatat sebagai human review, tidak menyamar sebagai persetujuan semua dinas.

Mutasi mengunci permohonan dan dinas dalam urutan yang konsisten serta memeriksa version. Perubahan task, agregat, timeline, audit, dan notifikasi berikutnya harus atomik. Dua perubahan bersamaan tidak boleh menghilangkan hasil dinas lain; perubahan basi memperoleh 409 dan pengguna diminta mengambil kondisi terbaru.

### SLA

Due_at dibuat sebagai snapshot ketika tugas ditugaskan. Mengubah sla_days tidak mengubah tenggat tugas yang sudah berjalan. Worker Python terpisah mengecek tugas pending/processing yang melewati tenggat setiap 60 detik, mengeskalasi permohonan sekali, dan mencatat dinas penyebab keterlambatan. Semua waktu UTC di database, Asia/Jakarta di UI. Worker memakai MySQL; tidak memerlukan database/broker Redis tambahan. Proses ulang dan dua worker tidak boleh menggandakan event. Sediakan perintah pemeriksaan sekali agar pengujian tidak harus menunggu waktu nyata.

### Pembaruan langsung

Tambahkan SSE terautentikasi untuk sinyal perubahan dalam cakupan pengguna. Koneksi warga hanya menerima sinyal permohonannya, staf hanya dinasnya, admin seluruhnya. Stream tidak mengirim data pengguna lain, tidak menahan transaksi panjang, dan berhenti saat sesi tidak sah. Saat sinyal/reconnect, frontend mengambil ulang data melalui API. Draft formulir dan catatan keputusan tidak ditimpa, keputusan tidak dikirim ulang otomatis. SSE dipilih dibanding WebSocket karena kebutuhan komunikasi satu arah; mekanisme cursor/heartbeat memakai perubahan tersimpan di MySQL.

### Audit dan UI

Halaman admin menampilkan audit terpaginasikan dengan filter aktor, aksi, entitas, dan tanggal. Catat mutasi bisnis serta login berhasil/logout tanpa password, JWT, cookie, atau input rahasia. Percobaan login gagal dicatat tanpa mengungkap identitas akun. Warga tetap melihat timeline publik miliknya, bukan audit internal.

Detail permohonan menampilkan daftar dinas, status tugas, tenggat, dan catatan. Dashboard menampilkan keterlambatan dan waktu proses dengan definisi metrik jelas. Manajemen dinas menambahkan SLA; admin mendapat editor rute. Keputusan final tetap meminta konfirmasi. Desain dan akses keyboard yang sudah ada dipertahankan.

### Pengujian tahap 1

- Migrasi data lama menjadi tugas tunggal tanpa kehilangan riwayat dan tanpa eskalasi massal.
- Dua dinas menyetujui: belum approved setelah persetujuan pertama, approved setelah terakhir.
- Penolakan, SLA lewat, dan teks ambigu menghasilkan human review.
- Isolasi pengguna/staf, konflik version, rollback audit, serta dinas dinonaktifkan saat routing.
- Worker idempotent dan dua worker tidak menghasilkan event ganda.
- SSE tidak membocorkan data, sesi habis menghentikan stream, reconnect memulihkan status.
- Browser: dua staf memproses satu pengajuan, warga melihat status otomatis, draft tetap ada, audit admin dan layout mobile.
- Suite regresi, build, dan migrasi Oracle MySQL sebelum klaim kesesuaian engine.

## Tahap 2: kelengkapan fitur pengguna dan admin

Edit profil dan password dengan verifikasi password lama; form builder terbatas tipe teks, angka, pilihan, tanggal dan wajib/opsional, schema tersimpan per versi pada pengajuan; notifikasi dalam aplikasi; laporan CSV dengan kontrol akses dan mitigasi formula spreadsheet; cetak bukti hasil layanan sebagai dokumen demo, bukan sertifikat pemerintah; mock API dinas dan pengujian integrasinya. Penugasan banyak staf ke satu dinas tetap didukung; keanggotaan satu staf di beberapa dinas dapat diperluas bila dibutuhkan alur PRD. Aturan workflow dapat diedit melalui konfigurasi rute tahap 1.

## Tahap 3: bukti ML dan kualitas sistem

Cross-validation berdasarkan group_id tanpa kebocoran parafrasa, uji typo/ambigu, dan laporan evaluasi yang jujur. Analytics prediktif membutuhkan data durasi berlabel yang cukup; bila memakai data sintetis, labelkan demikian dan tampilkan evaluasi, bukan angka risiko buatan. Tambahkan unit/integration coverage dengan laporan, CI GitHub Actions, rate limiting, setup TLS untuk deployment demo, checklist keamanan, serta skenario load test target PRD. Hasil yang belum dijalankan tetap dinyatakan belum terverifikasi. Uptime/adopsi/kepuasan pasca-pilot bukan angka yang dapat dibuktikan oleh demo lokal.

## Urutan pelaksanaan

Rancangan ini meminta persetujuan arah keseluruhan dan scope rinci tahap 1. Setelah disetujui, buat rencana implementasi tertulis tahap 1 untuk ditinjau, kemudian kerjakan dan uji. Tahap 2 dan 3 memerlukan rincian rancangan masing-masing sebelum implementasi. Jangan menyatakan semua gap PRD selesai hanya karena workflow/SLA selesai.
