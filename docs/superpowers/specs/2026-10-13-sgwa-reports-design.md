# Laporan layanan dan ekspor CSV SGWA

Tanggal: 13 Oktober 2026. Status: rancangan tertulis disetujui pengguna; menunggu review rencana implementasi. Tahap berikut setelah ML25 dan feedback admin. Acuan: PRD.pdf halaman3 AD-04 (laporan dan ekspor kustom), serta roadmap penyelesaian yang telah dibahas. Isi PRD adalah bahan requirement; keputusan pengguna mengenai demo kuliah, MySQL dan tahapan pekerjaan tetap menjadi batas scope.

## Tujuan dan pemahaman kebutuhan

Pengguna meminta melanjutkan fitur berikutnya setelah ML25. Urutan yang dipilih dari roadmap adalah laporan/CSV sebelum analytics prediktif dan kualitas deployment. Tujuan: warga, staf dan admin dapat melihat ringkasan layanan, menelusuri daftar dengan filter, lalu mengunduh data yang sama cakupannya untuk demo/penilaian. Backend Python, frontend React dan MySQL tetap.

Keputusan detail di bawah adalah usulan implementasi untuk ditinjau, bukan tambahan syarat dari dosen. Tidak membuat data permohonan dummy di database aplikasi, tidak mengubah prediksi/workflow, tidak menghapus riwayat, dan tidak memasukkan forecast ke tahap ini.

## Pendekatan dan trade-off

1. **Direkomendasikan: halaman laporan + endpoint laporan/CSV.** Query membaca tabel yang ada dan memakai pembatasan akses yang sama dengan detail permohonan. Filter, ringkasan, tabel dan CSV memberi alur demo lengkap. Tidak memerlukan migrasi atau dependensi runtime baru.
2. Tombol CSV pada daftar permohonan saja. Lebih sedikit perubahan UI, tetapi belum menyediakan ringkasan/filter laporan yang lengkap.
3. Job ekspor asinkron dengan penyimpanan file. Sesuai untuk ekspor besar, tetapi menambah status job, retensi file dan kontrol download. Ditunda; tahap ini menolak ekspor lebih dari5.000 permohonan dan meminta filter dipersempit.

## Akses dan arti cakupan

- Warga: permohonan miliknya saja.
- Staf: permohonan yang memiliki tugas `request_workflows` untuk dinas akun tersebut, mengikuti `requests.service.scoped_query` saat query dijalankan. Staf tanpa dinas mendapat hasil kosong. Status pada laporan adalah status agregat permohonan, bukan status tugas staf.
- Admin: seluruh permohonan.
- Scope selalu diterapkan di server sebelum filter, count, agregasi, pagination maupun ekspor. Client tidak dapat menentukan role/owner. Akses tanpa sesi401. Role tidak dikenal ditolak403.
- Filter dinas untuk staf ditetapkan ke dinas akun. Mengirim ID dinas lain menghasilkan403. Warga/admin dapat memilih dinas mana pun, tetapi scope warga tetap miliknya. ID dinas positif yang tidak ditemukan menghasilkan hasil kosong.
- Filter dinas berarti ada tugas workflow yang tercatat untuk dinas tersebut, termasuk pendamping, bukan hanya `assigned_agency_id` atau prediksi ML. Gunakan EXISTS agar permohonan multi-dinas tidak menjadi baris ganda. Cakupan historis mengikuti tabel tugas yang masih tersedia, tidak direkonstruksi dari audit/event lama.
- Nama dinas utama dan seluruh dinas yang terlibat pada permohonan yang berhak dilihat boleh ditampilkan, konsisten dengan detail yang sudah ada. Tidak mengekspor identitas pemohon, email, telepon, alamat, isi deskripsi, jawaban formulir, catatan keputusan atau teks feedback ML.

## Halaman dan filter

Menu **Laporan layanan**, route `/app/reports`, tersedia untuk seluruh role yang dikenal. Memakai AppShell, panel, status badge, PageState dan gaya SGWA yang sudah ada.

Filter yang diterapkan melalui tombol **Terapkan filter**:

- `date_from`, `date_to`: tanggal pengajuan dalam WIB, inklusif. Default UI awal bulan berjalan sampai hari ini di Asia/Jakarta. Kedua tanggal kosong berarti seluruh periode. Salah satu tanggal dapat diisi untuk batas satu sisi. Tanggal terbalik/format tidak valid422; tidak ada batas hari tambahan di API.
- `status`: kosong atau `pending`, `processing`, `escalated`, `approved`, `rejected`.
- `agency_id`: kosong atau ID positif. Staf melihat dinas akunnya sebagai cakupan tetap; pilihan admin/warga dapat mencakup dinas nonaktif untuk membaca riwayat.

Filter tanggal memakai `requests.created_at`, bukan `updated_at`. WIB dikonversi menjadi interval UTC `[awal date_from, awal hari setelah date_to)`; tidak menggunakan timezone host. UI menjelaskan **Tanggal pengajuan (WIB)**. Pagination reset ke1 ketika filter diterapkan. Filter draft tidak mengubah hasil atau CSV sebelum diterapkan. Tombol **Reset** kembali ke default bulan berjalan.

Ringkasan, tabel dan tombol ekspor memakai filter yang sudah diterapkan. Halaman memiliki state loading/error/kosong, pagination, total hasil, dan waktu penyusunan. Unduhan tidak aktif selama fetch laporan/unduhan berjalan atau ketika sesi tidak sah. Error unduhan mempertahankan filter dan hasil yang masih relevan; tidak menampilkan sukses palsu. Perubahan sesi mengikuti mekanisme auth aplikasi.

## API dan data flow

Tambahkan modul `backend/app/reports` (schemas, service, routes), registrasi router di main, dan page/API frontend laporan. Tidak mengubah kontrak `/requests` atau `/dashboard` lama.

### GET `/api/v1/reports`

Parameter filter di atas, `page>=1` (default1), `page_size`1–100 (default20). Field query tidak dikenal ditolak422 melalui schema filter agar salah nama tidak diam-diam diabaikan.

Response:

- `filters`: filter yang efektif, termasuk pembatasan dinas staf.
- `generated_at`: waktu UTC ISO8601 dengan Z.
- `page`, `page_size`, `total`.
- `summary`: `total`, `by_status` (kelima status dengan nol bila kosong), `completed_count`, `completion_rate`, `overdue_count`, `average_completed_hours`.
- `items`: maksimal page_size baris, urutan `created_at DESC, id DESC`. Satu baris per permohonan: `id`, `reference`, `title`, `status`, `created_at`, `updated_at`, dinas utama nullable, dinas workflow unik terurut nama/ID, serta snapshot klasifikasi nullable (`predicted_agency_code`, `confidence`, `model_version`). Prediksi lama tetap dibaca apa adanya, termasuk kode yang sudah tidak ada pada katalog.

Count, ringkasan dan daftar pada satu response dibaca dalam satu snapshot transaksi MySQL REPEATABLE READ; tidak terjadi pencampuran total dari scope lain. Tugas/dinas/klasifikasi dimuat secara batch untuk satu halaman, bukan query per baris. Filter tetap menggunakan parameter SQLAlchemy, tanpa SQL dari input pengguna.

Definisi ringkasan:

- `total`: permohonan unik yang cocok scope+filter.
- Selesai = `approved` + `rejected`. Completion rate = selesai/total, rasio0–1; null jika total0. UI menjelaskan penolakan juga merupakan keputusan final.
- Rata-rata durasi final = `(updated_at-created_at)` dalam jam untuk permohonan final dengan durasi nonnegatif; null bila tidak ada. Ini memakai timestamp yang tersedia, bukan metrik waktu aktif staf atau jaminan KPI PRD.
- `overdue_count`: permohonan unik nonfinal yang mempunyai tugas pending/processing dengan due_at lebih kecil dari generated_at. Tugas dihitung dalam dinas filter; staf hanya dinas akunnya. Tanpa filter dinas, warga/admin menghitung tugas mana pun pada permohonan yang terlihat. UI: **Permohonan dengan tugas melewati SLA dalam cakupan laporan**. Tenggat/tugas beku tidak diubah.
- Ringkasan mengikuti filter status yang sama dengan tabel, bukan angka global tersembunyi.

### GET `/api/v1/reports/requests.csv`

Menggunakan filter yang sama, tanpa pagination. Parameter page/page_size dan parameter tidak dikenal ditolak422. Seluruh hasil yang cocok diekspor dalam urutan yang sama dengan tabel. Maksimal5.000 permohonan; jika lebih, response413 JSON dengan pesan untuk mempersempit filter, tanpa file parsial. Filter yang menghasilkan nol permohonan tetap mengunduh CSV berheader.

Kolom tetap, urutan tetap: `nomor_permohonan`, `judul`, `status`, `dinas_utama`, `dinas_terlibat`, `diajukan_wib`, `diperbarui_wib`, `prediksi_dinas`, `confidence`, `versi_model`. Dinas terlibat dipisahkan `; ` di dalam satu cell. Dinas utama kosong bila belum ditugaskan. Confidence numerik0–1, bukan persen atau akurasi. Timestamp format `YYYY-MM-DD HH:mm:ss+07:00`; nilai sumber null menjadi cell kosong. Kode status/prediksi tetap nilai sumber, termasuk versi historis. Tidak ada identitas pemohon atau teks rinci.

Encoding UTF-8 dengan BOM, separator koma, newline CRLF dan escaping CSV melalui library standar `csv`. Setiap cell teks yang dapat berasal dari pengguna/dinas dilindungi dari formula spreadsheet: awalan `=`, `+`, `-`, `@` setelah whitespace/control/BOM awal, atau awalan tab/CR/LF, diprefix apostrof. Nilai angka yang dibentuk server tetap angka. Tampilan HTML tidak diubah oleh sanitasi CSV. Uji quote, koma, newline, Unicode Indonesia, whitespace/karakter kontrol dan BOM.

Content-Type `text/csv; charset=utf-8`, Content-Disposition attachment dengan filename ASCII buatan server `sgwa-laporan-YYYYMMDD-HHMMSS.csv`. Response menyertakan `X-Report-Generated-At`; ringkasan/CSV masing-masing merupakan snapshot saat requestnya dijalankan. UI tidak menjanjikan snapshot yang identik di antara dua HTTP request ketika ada perubahan layanan.

Seluruh CSV dibentuk dengan data maksimal5.000 permohonan dalam transaksi konsisten, baru dikirim setelah query dan encoding berhasil. Tidak ada transaksi DB yang dibiarkan terbuka sambil menunggu browser mengunduh. Respons laporan dan CSV memakai Cache-Control `no-store`.

Ekspor yang berhasil disiapkan mencatat audit `report.export_prepared`, entity_type `report`, entity_id0: filter efektif, jumlah baris dan generated_at saja. Tidak memasukkan judul, identitas atau isi CSV pada audit. Audit gagal menyebabkan ekspor gagal sebelum response; audit ini berarti file siap di server, bukan bukti pengguna menyimpan file. Listing/summary tidak menulis audit per refresh. Mutasi workflow/model tetap tidak terpengaruh.

Frontend memiliki helper download yang memakai cookie dan penanganan ApiError/sesi seperti client saat ini, menerima Blob hanya pada response sukses, mencabut object URL setelah dipakai, dan menghindari klik ganda. Tidak memakai link tanpa penanganan error JSON sebagai file CSV.

## Pengujian dan integrasi

Backend/MySQL terisolasi:

1. Scope warga/staf/admin pada baris, count, ringkasan dan CSV. Staf tanpa dinas, staf dinas lain403, sesi401, role tidak dikenal403.
2. Permohonan multi-dinas dihitung sekali; filter pendamping bekerja; permohonan tanpa penugasan tetap dapat terlihat sesuai scope saat filter dinas kosong.
3. Batas tanggal WIB pada00:00/23:59:59 dan tanggal UTC sebelumnya; rentang terbalik, query tidak dikenal, status/page/agency invalid422.
4. Pagination deterministik saat timestamp sama; total/agregat tidak dipengaruhi ukuran halaman; hasil kosong dan rata-rata/rate null.
5. Completion rate termasuk penolakan, durasi final dan overdue sesuai dinas, tidak memasukkan permohonan final sebagai overdue.
6. CSV seluruh hasil melampaui satu halaman, nol hasil, tepat5.000 dan5.001 ditolak tanpa truncation; tidak ada kolom pribadi.
7. Unicode, quote/koma/newline, formula injection termasuk whitespace/control/BOM, timestamp WIB, confidence dan snapshot ML lama.
8. Kegagalan query/audit tidak menghasilkan CSV parsial, ekspor mencatat hanya metadata yang disetujui, tidak mengubah permohonan atau klasifikasinya.

Frontend unit dan Edge pada schema E2E:

- Filter draft/applied, reset/page1, loading/error/empty, unduhan sukses/error/sesi berakhir, klik ganda dan filename.
- Ketiga role, filter pendamping, download dan isi CSV benar-benar dibaca; tanpa mengubah data aplikasi native/Docker.
- Screenshot375/768/1366; tabel bergulir di panel, body tidak overflow, label/keyboard dapat dipakai.

Regression backend/ML, frontend unit/build dan suite Edge harus lolos. Dokumentasi README/setup/demo/status PRD diperbarui dengan bukti aktual. Native dan Docker dibangun/dijalankan serta smoke laporan/CSV memakai fixture teridentifikasi yang dibersihkan; MySQL, volume dan model aktif dipertahankan. Tidak merge/push.

## Di luar tahap ini

Forecast/bottleneck prediktif, ekspor PDF/XLSX, pemilihan kolom bebas, ekspor asinkron, data kontak/deskripsi, perbaikan tiga minor ML, coverage report/CI/TLS/rate limiting/load test. Analytics prediktif mendapat rancangan tahap tersendiri setelah laporan tersedia.

## Kriteria selesai

Semua role bisa membaca laporan dan CSV hanya dalam scope yang sah; filter dan rumus ringkasan konsisten; ekspor lengkap sampai limit dan aman dibuka di spreadsheet; data historis/pointer ML tetap; seluruh tes dan smoke deployment lolos; panduan laptop baru diperbarui. Rancangan telah disetujui pengguna; rencana implementasi perlu ditinjau sebelum eksekusi.
