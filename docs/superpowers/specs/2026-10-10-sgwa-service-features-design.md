# SGWA tahap A — profil dan fitur layanan

Tanggal: 10 Oktober 2026. Status: **rencana disetujui dan fitur diimplementasikan; review kode akhir sedang dilakukan**.
Dokumen induk: [roadmap penyelesaian](2026-10-10-sgwa-completion-roadmap.md).

## Tujuan dan batas

Menyelesaikan fitur layanan yang belum tersedia untuk demo akademik: profil/ganti password, form builder, notifikasi persisten, bukti hasil, dan mock API. FastAPI/React, MySQL, Argon2, cookie/CSRF, workflow paralel, SSE dan audit dipertahankan. ML 25 kelas, laporan/forecast dan deployment quality dikerjakan pada tahap berikutnya.

Seluruh fitur tersedia pada frontend dan backend, bukan hanya endpoint. Tampilan mengikuti desain aplikasi yang sudah ada. Tidak menambahkan integrasi pemerintah produksi, upload dokumen, email/SMS, pembayaran atau tanda tangan elektronik resmi.

## Profil dan ganti password

- Semua role dapat melihat/mengubah nama, nomor telepon opsional dan alamat opsional miliknya. Email, role dan penugasan dinas tidak dapat diubah lewat endpoint profil. Nama wajib 2–150 karakter, telepon maksimal 30, alamat maksimal 500.
- Ganti password memerlukan password saat ini, password baru 10–128 karakter dan konfirmasi pada UI. Password baru harus berbeda. Verifikasi dan hashing tetap Argon2. Respons/audit tidak menyimpan password atau hash.
- Tambahkan `users.session_version` integer default 1. JWT sesi baru membawa versi tersebut. Ganti password mengunci baris user, mengubah hash dan menaikkan versi dalam satu transaksi. Semua sesi sebelumnya berakhir; pengguna diarahkan login kembali. JWT lama yang tidak memiliki versi juga ditolak setelah migrasi, sehingga pengguna lama perlu login sekali lagi.
- Pemeriksaan versi dilakukan pada dependency autentikasi, pembentukan CSRF untuk sesi login dan autentikasi SSE. SSE mengirim session-invalid ketika versi berubah. Tidak cukup hanya menghapus cookie pada browser yang melakukan perubahan.
- API: `GET /profile`, `PATCH /profile`, `POST /profile/password`, semuanya di bawah `/api/v1`. Password salah ditolak, percobaan basi/concurrent tidak boleh mengembalikan hash lama. Penonaktifan akun tetap berlaku.

## Form builder layanan

- Admin mengelola definisi formulir untuk layanan yang terhubung satu instansi aktif. Warga memilih layanan secara opsional; pengajuan judul/deskripsi yang ada tetap tersedia. Pilihan layanan bukan pengganti keputusan ML. Jika kelas prediksi bertentangan dengan instansi formulir, pengajuan masuk review admin dengan alasan yang terlihat.
- Jenis field: teks pendek, paragraf, angka, tanggal, pilihan tunggal dan checkbox boolean. Setiap field memiliki key stabil, label, required dan batas/opsi yang sesuai jenisnya. Maksimal 30 field; key unik, tanpa ekspresi/script/HTML yang dieksekusi.
- Pisahkan definisi `service_forms` (agency_id, title, active, current_version) dari `service_form_versions` (form_id, version, schema JSON, state draft/published, created_by, created_at, published_at nullable). Kombinasi form_id/version unik. Versi dipublikasikan atomik dan immutable; setiap pembaruan membuat versi baru. Draft dapat diedit sebelum publish. UI menyediakan preview dan validasi sebelum publish.
- Tambahkan referensi versi formulir dan `form_answers` JSON pada permohonan. Formulir/versi yang telah dipakai tidak dihapus; admin dapat menonaktifkan layanan. Permohonan menyimpan versi persis saat dikirim. Pengiriman versi yang sudah tidak menjadi versi aktif ditolak 409 dan meminta pengguna memuat formulir terbaru; jawaban pengguna dipertahankan pada UI untuk ditinjau.
- Backend memvalidasi jawaban menggunakan schema versi tersimpan: field wajib, tipe, panjang, opsi dan rentang. Field tak dikenal ditolak. Deskripsi tetap input classifier; jawaban terstruktur tidak otomatis dipakai sebagai fitur ML tanpa rancangan dataset baru.
- API admin: daftar/detail, buat, ubah draft, publish dan nonaktifkan `/service-forms`. API warga mengambil daftar aktif serta versi untuk rendering. Submit `/requests` menerima pasangan form_version_id/answers opsional; tidak boleh mengirim salah satu saja.

## Notifikasi persisten

- Tabel `notifications`: id, user_id, event_key, kind, title, request_id nullable, created_at, read_at nullable. Unik `(user_id,event_key)` untuk mencegah duplikasi retry. Isi ringkas tanpa menyalin seluruh permohonan.
- Trigger: pengajuan diterima ke warga dan staf instansi yang mendapat tugas; pengalihan ke staf baru; perubahan status/keputusan ke warga; eskalasi ke admin; hasil akhir ke warga. Tidak ada broadcast lintas dinas atau pengguna tanpa akses.
- Notifikasi dibuat pada transaksi yang sama dengan perubahan permohonan, task, timeline dan audit. Refactor lokasi commit pada service workflow/submit/SLA agar kegagalan notifikasi membatalkan seluruh perubahan, bukan menyimpan status lalu gagal membuat notifikasi. Worker berulang tidak menduplikasi notifikasi eskalasi.
- API `/notifications` terpaginasikan, unread count, tandai satu atau semua sebagai dibaca. Mutasi hanya untuk pemilik. Respons tidak boleh membuka informasi request yang sudah tidak dapat diakses; judul generik tetap, tautan hanya jika actor masih punya scope.
- SSE memakai revisi notification milik actor di samping revisi request yang ada. Menu lonceng/unread dan daftar notifikasi diperbarui otomatis. Notifikasi tetap ada setelah reload, logout/login dan restart API. SSE tetap autentik dan tidak membawa daftar notifikasi pengguna lain.

## Bukti hasil

- Permohonan berstatus approved/rejected memiliki bukti hasil dengan nomor unik, nomor referensi permohonan, pemohon, status, waktu finalisasi, ringkasan keputusan dan daftar keputusan instansi. Kasus pending/processing/escalated belum memiliki bukti hasil.
- Tabel `result_documents` memiliki satu snapshot immutable per keputusan final, request_id unik dan nomor dokumen unik. Snapshot dibuat pada transaksi keputusan final; retry tidak membuat dokumen kedua. Workflow saat ini tidak membuka kembali status final, sehingga revisi dokumen belum diperlukan.
- UI halaman bukti menyediakan CSS cetak dan tombol cetak/simpan PDF melalui browser. Belum menyediakan file PDF server atau verifikasi publik. Label **Bukti hasil demonstrasi akademik — bukan dokumen resmi** selalu terlihat, termasuk pada cetakan.
- Akses melalui `/requests/{id}/result` mengikuti scope request: pemilik warga, staf terkait, atau admin. Nomor dokumen tidak melewati otorisasi. Dokumen final yang sudah ada sebelum migrasi dibuat secara idempotent dari keputusan historis yang tersedia dan diberi keterangan hasil konversi; informasi yang tidak tercatat tidak dikarang.

## Mock API

- Endpoint terautentikasi untuk simulasi verifikasi data layanan, dengan mode sukses/tidak cocok/tidak tersedia. Fixture sintetis tetap dan hasil deterministik; tidak menghubungi sistem pemerintah nyata.
- Mock tidak mengubah keputusan ML atau menyetujui tugas otomatis. Staf/admin menjalankan pemeriksaan untuk request yang dapat diakses; UI menunjukkan **simulasi** dan hasilnya sebagai informasi untuk keputusan manusia.
- Tabel `mock_checks`: request_id, actor_id, check_type, outcome, checked_at, hasil sintetis ringkas, idempotency_key. Kombinasi actor_id/idempotency_key unik. Request citizen tidak dapat memilih role/actor atau menulis hasil pemeriksaan sendiri. Retry memiliki idempotency key agar tidak membuat rekaman berulang tanpa sengaja; key yang dipakai dengan payload berbeda ditolak 409.
- API `/requests/{id}/mock-checks` mendukung riwayat dan menjalankan pemeriksaan; jenis pemeriksaan awal identitas, kelengkapan izin dan verifikasi layanan umum. Jenis lain dapat ditambahkan kemudian tanpa mengklaim integrasi nyata untuk semua 25 instansi.

## Migrasi dan integrasi

Tambahkan kolom nullable profil/form pada tabel lama, session_version default 1, serta tabel formulir/versi, notifikasi, bukti dan mock melalui Alembic berurutan. Pertahankan seluruh ID dinas, akun, permohonan dan audit. Sesi lama harus login ulang; password akun lama tidak diganti oleh seed. Native dan Docker memakai migrasi yang sama.

Daftar navigasi: Profil untuk semua role, Notifikasi untuk semua role, Formulir layanan untuk admin. NewRequest merender field layanan yang dipilih. RequestDetail menampilkan jawaban versi lama, riwayat simulasi bagi staf/admin dan tautan bukti hasil. Status PRD/README diperbarui hanya setelah verifikasi aktual.

## Kriteria penerimaan dan pengujian

1. Profil dapat diperbarui tanpa mengubah role/email/dinas. Akun lain tidak dapat dibaca/diubah. Password salah ditolak; perubahan benar membatalkan sesi HTTP dan SSE pada dua browser.
2. Admin mempublikasikan form; warga mengirim jawaban tervalidasi. Form versi lama tetap terbaca setelah publish versi baru. Jawaban invalid, key tak dikenal, versi basi dan form nonaktif ditolak dengan pesan yang dapat ditindaklanjuti.
3. Pengajuan teks lama tetap berjalan. Pilihan form yang bertentangan dengan kelas ML masuk review; tidak memaksa rute salah. Pengajuan tanpa form tetap kompatibel dengan klien yang ada.
4. Mutasi workflow dan SLA menghasilkan notifikasi tepat scope, tanpa duplikasi retry. Uji rollback jika insert notifikasi gagal serta dua keputusan dinas bersamaan. Unread persisten dan SSE memperbarui UI.
5. Bukti muncul hanya setelah hasil final, dapat dicetak, memuat label demo, dan snapshot tidak berubah saat profil/nama dinas berubah. Uji backfill keputusan lama, penolakan, idempotensi dan akses lintas akun.
6. Mock sukses/gagal/tidak tersedia terlihat sebagai simulasi. Tidak mengubah status request secara otomatis, tidak melakukan panggilan eksternal, dan tidak membuka scope dinas lain.
7. Migrasi sukses pada schema MySQL kosong dan database baseline; seed berulang mempertahankan 25 instansi tanpa mengganti password. Backend suite dan build frontend lolos; browser menguji alur form→submit→notifikasi→keputusan→cetak serta perubahan password lintas sesi. Uji juga melalui proxy Docker dan SSE.

## Review yang diperlukan

Pengguna meminta dilanjutkan dengan skill executing-plans. Metode eksekusi langsung di sesi ini dipertahankan. Rencana implementasi menyertakan file, migrasi, test dan urutan eksekusi; perubahan produk dimulai setelah review rencana tertulis sesuai handoff writing-plans. Training 25 kelas serta feedback admin berada pada tahap B, bukan kriteria selesai tahap A.
