# SGWA - Spesifikasi proyek akhir semester

Tanggal: 4 Oktober 2026
Status: Disetujui pengguna pada 4 Oktober 2026; menunggu review rencana implementasi.

## Tujuan dan batas wajib

Membangun web Smart Government Workflow Automation untuk demo dan penilaian proyek akhir semester dalam tujuh minggu. Pengguna mewajibkan AI/ML di dalam web dan MySQL sebagai database; backend Python disarankan. Ketentuan lainnya dalam PRD adalah referensi yang dapat disesuaikan, bukan seluruhnya kewajiban dosen.

Keberhasilan: mahasiswa bisa memperlihatkan pengajuan warga, klasifikasi ML, pemrosesan staf, status akhir, serta evaluasi model yang dapat dijelaskan. Data demo adalah data fiktif tanpa data pribadi warga nyata. Aplikasi tidak mengaku terhubung ke pemerintah atau siap produksi.

## Pilihan pendekatan

1. **Direkomendasikan: FastAPI, React/Vite, MySQL, scikit-learn.** Pemisahan antarmuka dan API memudahkan demo, sementara model Python dapat dilatih dan dievaluasi langsung. Konsekuensinya: dua proses pengembangan dan pengaturan autentikasi API.
2. **Django dengan template dan MySQL.** Lebih sedikit proses dan admin bawaan mempercepat CRUD. Antarmuka interaktif membutuhkan integrasi tambahan; pilihan baik bila penyederhanaan setup lebih penting.
3. **Web dengan layanan LLM eksternal.** Fleksibel untuk memahami teks, tetapi menambah biaya, ketergantungan jaringan, dan lebih sulit memperlihatkan proses pelatihan model sendiri. Tidak dipilih untuk inti demo.

## Cakupan versi demo

- Akun warga, staf, dan admin; login dan registrasi warga.
- Pengajuan judul dan deskripsi permohonan, tanpa form builder dinamis.
- Klasifikasi satu dinas utama: Dukcapil, Perizinan, Pajak, atau Kesehatan.
- Hasil klasifikasi, skor probabilitas, versi model, dan penanda pemeriksaan manual.
- Warga melihat daftar miliknya dan timeline detail.
- Staf melihat dan memproses permohonan dinasnya.
- Admin melihat semua permohonan, mengubah rute kasus eskalasi, mengelola dinas dan penugasan staf.
- Ringkasan jumlah permohonan per status/dinas dan audit setiap perubahan.
- Dataset, skrip pelatihan, laporan evaluasi, akun demo, dan panduan presentasi.

Ditunda: orkestrasi paralel lintas dinas, Celery/Redis, prediksi bottleneck, WebSocket, lampiran, sertifikat, email/SMS, pembayaran, integrasi dinas nyata, dan deployment publik. Memuat ulang daftar atau detail mengambil status terbaru; pembaruan otomatis dapat ditambahkan setelah alur inti stabil.

## Arsitektur dan batas modul

Backend: Python 3.11+ dan FastAPI, SQLAlchemy 2, Alembic, PyMySQL, Pydantic, PyJWT, dan hashing password Argon2. Frontend: React, TypeScript, Vite, React Router, Radix Themes untuk komponen aksesibel, dan satu keluarga ikon Phosphor. Database: MySQL 8.4; tidak memakai SQLite sebagai pengganti termasuk pada pengujian integrasi. Docker Compose menyediakan MySQL lokal secara opsional; instalasi MySQL lokal juga didukung. Nomor versi dependency dipastikan dan dikunci saat setup.

Backend merupakan modular monolith dengan modul auth, agencies, requests, workflow, audit, dan ML. API mengakses service; service memvalidasi aturan bisnis dan menjalankan transaksi melalui SQLAlchemy. ML memiliki kontrak prediksi tersendiri dan tidak mengubah database langsung. Frontend mengambil seluruh data aplikasi dari API, bukan data hardcoded yang menyamar sebagai backend.

Struktur: `backend/app/` untuk modul API dan bisnis; `backend/alembic/` untuk migrasi; `backend/tests/` untuk uji; `ml/data/`, `ml/train.py`, dan `ml/artifacts/` untuk dataset/model; `frontend/src/` untuk aplikasi; `docs/` untuk petunjuk dan laporan.

## Data

- `users`: id, name, email unik, password_hash, role, agency_id nullable, active, created_at. Satu staf ditugaskan ke satu dinas pada versi demo.
- `agencies`: id, code unik, name, description, active.
- `requests`: id, reference unik, citizen_id, title, description, assigned_agency_id nullable, status, version, created_at, updated_at.
- `classification_results`: id, request_id unik, predicted_agency_code, probabilities JSON, confidence, needs_review, model_version, created_at.
- `request_events`: id, request_id, actor_id nullable, event_type, from_status, to_status, note, created_at.
- `audit_logs`: id, actor_id nullable, action, entity_type, entity_id, changes JSON, created_at.

Semua waktu disimpan dalam UTC dan ditampilkan sebagai Asia/Jakarta. Dinas dengan permohonan historis dinonaktifkan, bukan dihapus. Rute ML memakai code dinas yang stabil; dinas baru tidak otomatis menjadi kelas model. Perubahan status, event, dan audit harus berhasil atau dibatalkan bersama dalam satu transaksi.

Ekstensibilitas dinas: admin dapat menambah dinas baru dan menugaskan staf tanpa migrasi skema atau perubahan kode. `agencies.code` adalah string unik, bukan enum empat dinas. Dinas baru dapat menerima reroute manual segera setelah aktif. Kelas classifier dibaca dari label dataset dan `classes_` model, bukan daftar empat kelas yang ditanam dalam kode. Agar routing otomatis mencakup dinas baru, tambahkan minimal 50 contoh berlabel dengan group_id, latih ulang, evaluasi, lalu pasang artefak model baru dan restart backend. Code dinas tidak dapat diubah setelah dibuat. Penambahan dinas tidak mengubah prediksi historis. Aktivasi model dilakukan melalui perintah lokal terdokumentasi, bukan upload model dari pengguna web.

## API dan kontrol akses

Prefix `/api/v1`. Endpoint auth: register, login, logout, me. Endpoint dinas: daftar dan pengelolaan admin. Endpoint permohonan: submit, daftar terpaginasikan, detail, perubahan status, dan reroute admin. Endpoint dashboard menyediakan agregat sesuai role. Endpoint ML menyediakan metadata dan evaluasi model untuk admin.

Registrasi selalu membuat role citizen. Token akses JWT berumur 30 menit, disimpan dalam cookie HttpOnly SameSite=Lax. HTTPS mengaktifkan Secure; development lokal menggunakan konfigurasi eksplisit. Request mutasi memakai token CSRF dan pemeriksaan Origin. Proxy Vite membuat panggilan development berada pada origin frontend yang sama. Logout menghapus cookie. Password dan secret tidak ditulis ke log atau repository.

Warga hanya dapat mengakses permohonannya; staf hanya permohonan yang ditugaskan ke dinasnya; admin mempunyai akses pengelolaan dan eskalasi. Server menegakkan aturan ini pada setiap endpoint. Percobaan mengakses detail di luar cakupan menghasilkan 404, aksi role terlarang 403, dan sesi tidak sah 401. Login gagal memberi pesan umum tanpa membocorkan keberadaan akun.

Judul 5-150 karakter, deskripsi 20-5000 karakter setelah trim. Email dinormalisasi sebelum pengecekan unik. Daftar menggunakan page >= 1 dan page_size 1-100. Payload tidak boleh menentukan owner, role, confidence, atau versi model sendiri.

## Alur dan state machine

Saat submit, service menjalankan prediksi model lokal dan menyimpan permohonan serta hasilnya. Prediksi dengan confidence >= 0,60, fitur teks dikenal, dan dinas aktif menghasilkan status pending dengan rute dinas. Confidence < 0,60, teks tanpa fitur dikenal, atau dinas tujuan tidak aktif menghasilkan escalated dan belum ditugaskan.

Staf dinas terkait dapat memindahkan pending ke processing, kemudian processing ke approved atau rejected dengan catatan wajib. Staf dapat memindahkan pending/processing ke escalated dengan alasan wajib. Admin dapat reroute escalated ke dinas aktif dan pending, atau memutus approved/rejected dengan catatan. Status akhir tidak dapat dibuka ulang pada versi demo.

Setiap mutasi menyertakan version yang dibaca klien. Update dengan versi basi menghasilkan 409; klien meminta pengguna memuat ulang. Tidak ada approval otomatis oleh AI. AI membantu routing, sedangkan staf/admin membuat keputusan layanan.

Jika model belum tersedia, submit menghasilkan 503 dengan pesan yang bisa ditindaklanjuti tanpa menyimpan permohonan setengah jadi. Tidak ada fallback klasifikasi palsu. Kegagalan MySQL menghasilkan error umum; antarmuka mempertahankan input agar pengguna dapat mencoba lagi.

## ML yang dapat dipertanggungjawabkan

Pipeline awal: TF-IDF word unigram/bigram dan Logistic Regression, random_state 42. Model mengembalikan empat probabilitas kelas; confidence adalah probabilitas tertinggi, bukan jaminan kebenaran. Tidak diperlukan LLM berbayar atau koneksi jaringan pada saat inferensi demo.

Dataset awal: minimal 200 contoh sintetis berbahasa Indonesia, minimal 50 per kelas, dengan label dan group_id untuk keluarga skenario/parafrasa. Data diberi keterangan sintetis. Pisahkan train/test 80:20 berdasarkan group_id sebelum fit vectorizer; kelompok parafrasa tidak boleh tersebar di kedua bagian. Uji mencakup variasi kalimat, typo ringan, dan contoh ambigu. Data uji tetap disimpan terpisah dari data train.

Laporan memuat jumlah contoh dan kelompok per split, precision/recall per kelas, macro-F1, confusion matrix, serta versi dan hash dataset/model. Target macro-F1 0,85 adalah sasaran, bukan hasil yang dijanjikan. Bila tidak tercapai, laporkan hasil sebenarnya dan analisis kesalahan. Skor data sintetis tidak diklaim mewakili permohonan warga nyata. Halaman admin menjelaskan keterbatasan ini.

## Desain antarmuka

Reading this as: portal layanan publik untuk warga dan demonstrasi akademik, dengan bahasa visual terpercaya, jelas, dan aksesibel.

DESIGN_VARIANCE 3; MOTION_INTENSITY 2; VISUAL_DENSITY 5. Dasar terang, teks gelap, aksen hijau tua, tipografi sans yang mudah dibaca. Warna status bersifat semantik dan disertai teks. Tidak menggunakan foto dekoratif, efek neon, atau animasi yang mengganggu formulir.

Halaman: beranda layanan, login/registrasi, ringkasan warga dan pengajuan baru, detail dengan timeline, antrean staf, serta dashboard/admin dinas/staf/evaluasi ML. Desktop memakai navigasi samping pada ruang kerja; mobile memakai navigasi ringkas. Form memiliki label, bantuan, pesan validasi, focus terlihat, status loading/error/empty, dan konfirmasi untuk keputusan akhir. Layout diuji pada lebar 375, 768, dan 1366 piksel; tidak ada scroll horizontal seluruh halaman.

Skill design-taste-frontend diterapkan pada beranda dan prinsip visual yang sesuai; aturan marketing tidak dipaksakan ke tabel dan alur aplikasi karena skill mengecualikan dashboard dan multi-step product UI.

## Pengujian dan kriteria demo

- Unit: threshold klasifikasi, input tanpa fitur, transisi status, aturan akses, dan validasi input.
- Integrasi pada MySQL: registrasi/login, isolasi warga, isolasi dinas, submit beserta prediksi, rollback transaksi, konflik versi, reroute, audit.
- Frontend: validasi pengajuan, sesi berakhir, data kosong/error, penanganan 409, dan pengiriman ulang setelah kegagalan.
- Browser: alur warga -> staf -> warga dan kasus eskalasi -> admin; navigasi keyboard serta tiga ukuran viewport.
- ML: evaluasi dapat direproduksi, tidak ada group_id yang beririsan antara train/test, laporan sesuai model yang dimuat.
- Build frontend, test backend, dan migrasi MySQL harus berhasil; batas pengujian yang tidak bisa dijalankan harus dilaporkan.

Tidak menjadikan target 1000 concurrent requests PRD sebagai syarat demo. Gunakan pemeriksaan performa alur demo lokal dan laporkan hasil tanpa klaim load test yang belum dijalankan.

## Urutan tujuh minggu

1. Fondasi: repository, MySQL, migrasi, autentikasi, kerangka frontend, dan dataset awal.
2. Alur pengajuan, akses role, daftar/detail, serta audit.
3. Pelatihan, evaluasi, integrasi prediksi, dan eskalasi confidence rendah.
4. Antrean staf, keputusan layanan, reroute admin, dan pengelolaan dinas/staf.
5. Penyempurnaan antarmuka responsif, dashboard, dan halaman evaluasi ML.
6. Uji integrasi, browser, perbaikan, dan dokumentasi setup.
7. Pembekuan fitur, latihan presentasi, laporan model, dan cadangan demo.

Urutan ini adalah alokasi proyek, bukan alasan menunda implementasi yang dapat diselesaikan lebih awal. Implementasi nanti dikerjakan langsung dalam sesi melalui executing-plans setelah review spesifikasi dan rencana selesai.

## Skenario presentasi

1. Login warga dan ajukan pengurusan KTP; tampilkan prediksi Dukcapil beserta skor.
2. Login staf Dukcapil; proses dan setujui, lalu lihat timeline sebagai warga.
3. Ajukan teks ambigu/tidak dikenal; tunjukkan eskalasi dan reroute oleh admin.
4. Buka evaluasi model, jelaskan fitur TF-IDF, training/test, dan batas data sintetis.
5. Perlihatkan kontrol akses dan audit perubahan.

## Dasar dokumentasi

Dokumentasi diperiksa melalui Context7 pada 4 Oktober 2026:
- FastAPI JWT dan dependencies: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- scikit-learn TF-IDF: https://scikit-learn.org/stable/modules/feature_extraction.html
- Pencegahan data leakage: https://scikit-learn.org/stable/common_pitfalls.html

## Hasil self-review

Scope dibatasi ke satu alur dengan routing satu dinas. Approval layanan tetap manual. Kelas model, threshold, hak akses, dan transisi sudah eksplisit. Seluruh penyimpanan aplikasi menggunakan MySQL; artefak model dan dataset adalah file. Tidak ada nilai metrik evaluasi atau hasil tes yang diklaim sebelum dijalankan. Repository saat penyusunan spesifikasi masih kosong dan belum diinisialisasi sebagai Git; spesifikasi belum di-commit.
