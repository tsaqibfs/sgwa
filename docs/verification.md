# Verifikasi SGWA

Tanggal: 5 Oktober 2026. Hasil ini berlaku pada environment lokal pengembangan, bukan load test produksi.

## Hasil aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Backend / ML (`scripts/test_backend.py`) | 33 tes lulus, tidak ada skipped ketika TEST_DATABASE_URL diaktifkan |
| Frontend unit (`npm --prefix frontend test -- --run`) | 4 tes lulus |
| Browser Edge (`npm --prefix frontend run e2e`) | 4 skenario lulus |
| TypeScript dan Vite build | Berhasil |
| Dependency Python (`pip check`) | Tidak ada dependency rusak |
| Audit npm setelah pembaruan Vitest 4.1.11 | 0 kerentanan |
| Training ML | Macro-F1 1,000 pada 40 teks test sintetis dari 8 kelompok |

Backend mencakup isolasi warga/staf, keamanan sesi dan CSRF, rollback saat pencatatan audit gagal, boundary confidence 0,60, fitur teks tidak dikenal, model tidak tersedia, dinas nonaktif, penambahan dinas, seed idempotent, migrasi upgrade/downgrade, serta perubahan bersamaan dengan tepat satu update berhasil.

Browser mencakup warga -> staf -> warga, admin membuat dinas dan reroute eskalasi, navigasi keyboard, viewport 375/768/1366 tanpa overflow halaman, serta draft yang tetap ada saat login ulang dalam tab yang sama. Screenshots diperiksa untuk layout desktop/mobile dan beranda.

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
