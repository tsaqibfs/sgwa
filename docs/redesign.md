# Redesign SGWA — 5 Oktober 2026

Arah disetujui pengguna: portal layanan publik modern dengan hijau pinus, putih hangat, beranda editorial, antrean sebagai fokus dashboard, dan akses mobile/keyboard yang jelas.

## Audit dan keputusan

- Kartu statistik seragam dan panduan samping yang tinggi mengurangi fokus antrean. Statistik kini memakai satu strip dengan pemisah; daftar permohonan memakai lebar konten; panduan dipindahkan ke bawah daftar.
- Font sistem dan banyak caption kecil membuat hierarki kurang khas. Judul memakai Bahnschrift jika tersedia, dengan fallback Segoe UI; isi tetap Segoe UI. Angka memakai tabular figures. Caption layanan diperbesar, warna teks pendukung diperjelas.
- Beranda memakai diagram routing dari cerita warga ke contoh dinas, lalu tindak lanjut petugas. Diagram hanya menjelaskan alur, bukan data pengajuan atau hasil prediksi nyata.
- Warna permukaan diselaraskan ke putih hangat dan hijau lembut. Warna status tetap mempunyai makna dan label teks.
- Formulir, autentikasi, daftar admin, timeline, dan evaluasi model menggunakan aturan visual bersama. React, Radix Themes, Phosphor, dan semua API tetap dipakai.
- Ditambahkan favicon SVG, metadata deskripsi, tautan lompat ke konten, serta halaman 404 dengan jalan kembali ke beranda. Animasi mengikuti preferensi reduced motion.
- Tes mobile menemukan tombol Masuk tersembunyi oleh aturan navigasi lama. Aturan diperbaiki dan akses tombol pada lebar 375 piksel diproteksi oleh tes browser.

## Verifikasi

Tes baru akses keyboard/404 gagal sebelum implementasi dan lulus sesudahnya. Regresi tombol Masuk mobile juga direproduksi sebelum perbaikan CSS. Pemeriksaan akhir: 4 tes unit frontend, 6 skenario Edge, dan build TypeScript/Vite lulus. Screenshot beranda dan dashboard diperiksa pada lebar 375, 768, dan 1366 piksel; tidak ada overflow halaman. Form pengajuan desktop juga diperiksa secara visual.

Backend dan model tidak diubah dalam redesign ini. Hasil pengujian database sebelumnya tetap mempunyai batas engine yang dijelaskan dalam `verification.md`.
