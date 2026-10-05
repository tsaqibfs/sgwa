# Model klasifikasi SGWA

Tujuan model adalah menentukan satu dinas tujuan dari teks permohonan Indonesia. Model tidak menyetujui/menolak layanan.

## Pipeline

TF-IDF unigram/bigram dengan sublinear TF → Logistic Regression (`C=4`, `max_iter=1000`, `random_state=42`). Inferensi mengembalikan probabilitas tiap kelas. Kelas dibaca dari model, sehingga tidak terikat empat kelas awal.

Confidence tertinggi minimal 0,60, fitur teks dikenal, dan dinas aktif: routing otomatis. Confidence di bawah threshold, tidak ada fitur dikenal, atau dinas tidak aktif: eskalasi tanpa tujuan yang ditugaskan. Probabilitas ini belum dikalibrasi terhadap populasi warga nyata.

## Data dan pembagian

`ml/data/requests.csv`: 200 contoh sintetis, 50 per kelas (dukcapil, pajak, perizinan, kesehatan). `ml/build_dataset.py` mendokumentasikan 10 skenario per kelas dan lima parafrasa tiap skenario. Semua parafrasa dari skenario yang sama mempunyai group_id sama.

Training memakai 80% kelompok tiap kelas; test 20%. Kelompok tidak beririsan. TF-IDF fit hanya pada train. Artefak menyimpan train/test CSV, hashes dataset/model, metadata, laporan precision/recall/F1 dan confusion matrix. Tidak ada data pribadi warga.

## Hasil baseline aktual

Training awal menghasilkan macro-F1 **1,000** pada **40** contoh test (8 kelompok), dengan 160 contoh training (32 kelompok). Nilai tinggi dapat terjadi karena dataset kecil, formal, dan memakai pola kalimat berulang. Walaupun parafrasa satu skenario dipisah sebagai kelompok, gaya kalimat bersama masih ada di kedua split. Ini tidak membuktikan generalisasi pada percakapan bebas, typo, slang, permohonan campuran, atau layanan pemerintah nyata.

Nilai dashboard berasal dari `evaluation.json` milik model yang dimuat, bukan angka hardcoded. Target 0,85 dari desain tetap sasaran; perubahan dataset dapat menghasilkan nilai lebih rendah dan harus dilaporkan apa adanya.

## Menambah kelas/dinas

1. Admin menambah dinas dengan kode tetap, misalnya `pendidikan`.
2. Tambahkan minimal 50 teks dengan label tersebut dan minimal lima group_id berbeda. Gunakan lebih banyak skenario daripada sekadar menyalin template.
3. Jalankan training: `python -m ml.train` dari virtual environment.
4. Periksa evaluasi, kesalahan, dan apakah kelompok test benar-benar berbeda.
5. Restart backend agar model baru dimuat sekali. Reroute manual ke dinas baru sudah tersedia sebelum training.

Probabilitas dan versi model lama tersimpan pada masing-masing permohonan; training ulang tidak mengubah riwayat.

## Pemeriksaan model

Artefak biner `model.joblib` tidak dikirim Git; buat melalui training. Loader memverifikasi hash dan kecocokan kelas/versi laporan. Joblib menggunakan pickle; hanya muat artefak yang dibuat lokal dan dipercaya. Tidak ada endpoint upload model.

Untuk pengembangan berikutnya: kumpulkan teks independen yang ditinjau manusia, tambah variasi bahasa dan kasus ambigu, bandingkan dengan dummy baseline, serta lakukan evaluasi eksternal. Perubahan ini bukan syarat demo awal.
