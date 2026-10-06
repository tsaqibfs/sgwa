# Verifikasi SGWA

Tanggal: 5 Oktober 2026. Hasil ini berlaku pada environment lokal pengembangan, bukan load test produksi.

## Hasil aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Backend / ML (`scripts/test_backend.py`) | 36 tes lulus, tidak ada skipped ketika TEST_DATABASE_URL diaktifkan |
| Frontend unit (`npm --prefix frontend test -- --run`) | 4 tes lulus |
| Browser Edge (`npm --prefix frontend run e2e`) | 6 skenario lulus setelah redesign |
| TypeScript dan Vite build | Berhasil |
| Dependency Python (`pip check`) | Tidak ada dependency rusak |
| Audit npm setelah pembaruan Vitest 4.1.11 | 0 kerentanan |
| Training ML | Macro-F1 1,000 pada 40 teks test sintetis dari 8 kelompok |

Backend mencakup isolasi warga/staf, keamanan sesi dan CSRF, rollback saat pencatatan audit gagal, boundary confidence 0,60, fitur teks tidak dikenal, model tidak tersedia, dinas nonaktif, penambahan dinas, seed idempotent, migrasi upgrade/downgrade, serta perubahan bersamaan dengan tepat satu update berhasil.

Browser mencakup warga -> staf -> warga, admin membuat dinas dan reroute eskalasi, navigasi keyboard, viewport 375/768/1366 tanpa overflow halaman, serta draft yang tetap ada saat login ulang dalam tab yang sama. Screenshots diperiksa untuk layout desktop/mobile dan beranda.

Redesign 5 Oktober 2026 juga memverifikasi tombol Masuk mobile, tautan lompat ke konten yang memindahkan fokus, dan halaman 404. Audit dan perubahan visual dicatat dalam [redesign.md](redesign.md).

## Review akhir dan perbaikan

Review independen menemukan tiga masalah penting. Ketiganya direproduksi dengan tes yang gagal sebelum implementasi perbaikan, kemudian seluruh suite di atas lulus:

- Semua setup destruktif tes sekarang memakai validator URL yang sama sebelum koneksi. Hanya backend MySQL dan nama `sgwa_test` dengan karakter alfanumerik/underscore diterima; URL aplikasi, SQLite, dan nama berisi encoded slash ditolak.
- Catatan keputusan dan target pengalihan disimpan dalam memory provider berdasarkan pengguna dan permohonan. Login ulang pada tab yang sama memulihkan draft; keputusan akhir tetap meminta konfirmasi baru. Draft dihapus setelah tindakan berhasil atau logout eksplisit. Tes browser membuktikan pemulihan catatan staf setelah sesi habis.
- Submit dan reroute membaca dinas dengan `SELECT FOR UPDATE` sampai transaksi selesai. Dua tes koneksi bersamaan membuktikan perubahan status dinas menunggu transaksi routing.

Temuan yang tidak dijadikan perubahan: pengujian Oracle MySQL tetap dicatat sebagai gap environment; beban/keamanan produksi dan data ML nyata berada di luar scope demo. Teks tanpa fitur dikenal tetap dieskalasi walaupun probabilitas tertinggi besar. Persistensi setelah reload penuh tidak disyaratkan dan tetap tidak didukung. Format kode padat dan komponen auth bersama adalah pertimbangan pemeliharaan; konsekuensinya refactor mungkin diperlukan saat scope bertambah. Tidak ada temuan penting yang dibiarkan tanpa perbaikan.

Hasil akhir disimpan pada branch lokal yang sudah ada. Repository baru belum memiliki remote atau branch tujuan integrasi, sehingga tidak ada push/merge/PR.

## Engine database yang benar-benar diuji

Server EnvKit aktif: **MariaDB 11.8.2**, melalui driver SQLAlchemy `mysql+pymysql`. Database aplikasi `sgwa_demo` dan database test `sgwa_test_codex` dibuat terpisah. Database lama `sgwa_db` tidak diubah.

Konfigurasi **Oracle MySQL 8.4** ada di `compose.yaml`, tetapi belum dijalankan pada mesin ini karena Docker engine tidak tersedia. Karena itu, tidak ada klaim bahwa migrasi atau suite telah diverifikasi pada Oracle MySQL 8.4. Jalankan konfigurasi tersebut dan suite yang sama jika penilaian mewajibkan engine MySQL secara harfiah.

## Keputusan implementasi

- Proyek baru dikerjakan pada branch `feat/sgwa-demo` di direktori yang dipilih pengguna; tidak membuat worktree duplikat. Konsekuensi: perubahan berada langsung di direktori proyek ini.
- ML dikerjakan lebih awal sambil menunggu layanan database. Interface dan urutan dependensi tetap dipertahankan.
- Ledger memakai PowerShell/Python karena helper skill mengasumsikan Bash/POSIX. Konsekuensi: pencatatan kemajuan tidak menggunakan script helper asli.
- Pengujian pengembangan memakai engine EnvKit yang tersedia dan menyatakan perbedaan MariaDB/MySQL secara eksplisit. Konsekuensi: kompatibilitas Oracle MySQL masih perlu dibuktikan dengan suite yang sama.
- Halaman register berbagi komponen Login; tidak ada duplikasi form auth.

## Batas bukti

Tidak dilakukan load test 1000 concurrent requests, penilaian keamanan produksi, integrasi pemerintah nyata, atau evaluasi ML pada data warga nyata. Draft hanya bertahan dalam memory tab; reload penuh menutup sesi aplikasi dan menghapus draft. Log test menampilkan peringatan deprecation adapter TestClient upstream; seluruh assertions tetap lulus.
`nVerifikasi terbaru Oracle MySQL dan tahap pertama: [phase-one-verification.md](phase-one-verification.md). Catatan sebelumnya adalah riwayat pengujian, bukan status engine saat ini.
