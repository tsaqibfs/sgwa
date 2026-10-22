# ML 25 kelas dan pembelajaran dari koreksi

Classifier memilih satu kelas utama dari 25 kode katalog resmi. Workflow dapat melibatkan beberapa dinas. ML tidak menyetujui atau menolak layanan.

## Data dan hasil aktual

`ml/data/requests.csv`: 2.500 contoh **sintetis**, 100 per kelas, 10 keluarga skenario per kelas. Normalisasi `id-v1`: Unicode NFKC, lowercase, whitespace dan alias token konservatif (`jln`, `bnyk`, `lampmer`). Negasi/nama lokasi dipertahankan; tanpa fuzzy typo atau NER.

TF-IDF unigram/bigram sublinear → Logistic Regression (`C=4`, `max_iter=1000`, seed42). Holdout tetap `ml/data/holdout.json`: 500 contoh/50 kelompok. Training dasar: 2.000 contoh/200 kelompok. StratifiedGroupKFold lima fold pada training, TF-IDF di-fit ulang setiap fold. Feedback satu permohonan/hash/family dikelompokkan; konflik label ditolak; overlap holdout dikeluarkan.

Macro-F1 holdout **0,5463865546**, belum mencapai target0,85. Threshold dipilih dari validasi OOF pada0,70–0,95 dengan precision accepted minimal0,90 dan minimal25 contoh accepted. Baseline hanya2 accepted pada0,70, precision1,00, coverage0,10%: **routing otomatis nonaktif**. Pengajuan masuk review admin meskipun rekomendasi ML berconfidence tinggi. Confidence belum dikalibrasi pada populasi warga nyata.

Dashboard membaca laporan aktual: skor setiap kelas, confusion matrix, CV mean/std, threshold/coverage dan sumber data. Evaluasi tetap berlabel **holdout sintetis**, juga jika training memakai feedback nyata. Peningkatan skor tidak dijanjikan.

## Koreksi dan verifikasi admin

1. Detail permohonan → **Koreksi klasifikasi untuk training**: pilih kelas utama, sunting teks tanpa identitas pribadi, pilih asal data secara eksplisit, isi alasan. Kode keluarga opsional menyatukan parafrasa.
2. Simpan koreksi; dinas tujuan, keputusan dan prediksi awal tidak berubah.
3. **Feedback klasifikasi**: isi catatan dan verifikasi/tolak. Hanya revisi terkini terverifikasi menjadi data training. Revisi baru menyupersede yang lama.

MySQL menyimpan snapshot teks/prediksi awal, label, sumber, pelaku, pemeriksa dan waktu. Prediksi sendiri dan pengalihan workflow bukan ground truth. Konflik409 meminta membaca revisi terbaru; draft teks tetap tersimpan. Riwayat hanya dapat diakses admin.

## Training kandidat

Native dari root proyek:

```powershell
.\.venv\Scripts\python.exe -m scripts.train_candidate --actor-email admin@demo.sgwa.id
```

Docker:

```powershell
docker compose --env-file .env.docker -f compose.docker.yaml run --rm init python -m scripts.train_candidate --actor-email admin@demo.sgwa.id
```

Email harus admin aktif. CLI mengambil snapshot feedback, menulis manifest/hash dan artefak immutable, mendaftarkan **kandidat**, tanpa mengubah model aktif. Training gagal tercatat dan exit nonzero. Gunakan email operator sebenarnya jika akun demo tidak tersedia.

Halaman **Model ML** → **Lihat evaluasi** → tinjau sumber/CV/holdout → isi alasan → **Aktifkan**. Artefak harus lengkap, checksum cocok, tepat25 kelas, holdout sama; penurunan macro-F1 lebih dari0,02 terhadap model aktif ditolak. Skor di bawah0,85 tetap diberi peringatan. Revision pointer melindungi aktivasi bersamaan.

**Rollback** hanya ke versi yang pernah aktif, setelah membaca evaluasi dan mengisi alasan. Pengajuan berikutnya memakai versi baru tanpa restart API; prediksi historis tetap. Tidak ada pembelajaran online setiap laporan.

## Bootstrap, backup dan pemulihan

Setup: migrasi → seed → `python -m scripts.bootstrap_ml` → backfill. Instalasi pertama menyalin model lama ke archive dan mengaktifkan model25. Startup selanjutnya memvalidasi serta mempertahankan pilihan admin dan kandidat. `python -m ml.train` untuk artefak pengembangan; aplikasi memakai CLI kandidat.

Backup **database dan seluruh MODEL_DIR** bersama. Model di `MODEL_DIR/versions/<id>/`; metadata/evaluation/manifest/train/test/model memiliki checksum. Joblib memakai pickle: hanya artefak training lokal tepercaya, tanpa upload model.

File aktif hilang/rusak → inferensi503, bootstrap gagal tanpa retraining/fallback diam-diam. Pulihkan backup atau rollback admin ke artefak valid; daftar versi tetap tersedia. Perubahan kamus memerlukan versi normalizer baru dan retraining; jangan mengedit artefak aktif.

Multi-label, mapping urusan, ekstraksi lokasi dan branding Lamongan belum diimplementasikan.
