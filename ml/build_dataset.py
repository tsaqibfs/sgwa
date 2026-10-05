"""Reproducible synthetic teaching dataset. Groups preserve paraphrase isolation."""
import csv
from pathlib import Path

SCENARIOS = {
 'dukcapil': [
  'mengurus KTP elektronik yang hilang dan kartu identitas penduduk',
  'mengubah alamat domisili pada kartu keluarga setelah pindah rumah',
  'membuat akta kelahiran anak dan mendaftarkan anggota keluarga',
  'mengurus surat kematian anggota keluarga di catatan sipil',
  'memperbaiki nama dan tanggal lahir pada dokumen kependudukan',
  'mendapatkan surat pindah penduduk antar kabupaten',
  'mencatat perkawinan dan memperbarui status di kartu keluarga',
  'mencetak ulang kartu keluarga yang rusak',
  'merekam data biometrik KTP untuk penduduk usia tujuh belas tahun',
  'membuat kartu identitas anak dan validasi nomor induk kependudukan'],
 'pajak': [
  'memperbaiki tagihan pajak bumi bangunan rumah yang salah luas tanah',
  'mendaftarkan objek pajak daerah untuk restoran baru',
  'meminta penjelasan pembayaran tunggakan pajak reklame usaha',
  'memperbarui nama wajib pajak pada SPPT bangunan',
  'mengajukan pengurangan denda pajak daerah karena pembayaran terlambat',
  'mengurus bukti pembayaran pajak hotel yang tidak tercatat',
  'mendaftarkan nomor pokok wajib pajak daerah untuk perusahaan',
  'melaporkan perhitungan pajak parkir dan omzet usaha',
  'memohon koreksi nilai jual objek pajak tanah',
  'menanyakan pajak hiburan dan pelaporan pendapatan tempat wisata'],
 'perizinan': [
  'mengurus izin usaha toko sembako dan nomor induk berusaha',
  'mengajukan persetujuan bangunan gedung untuk pembangunan rumah',
  'memperpanjang izin operasional usaha restoran',
  'mengurus izin pemasangan reklame dan papan nama toko',
  'mengajukan izin lokasi dan persetujuan kegiatan usaha baru',
  'memeriksa persyaratan perizinan industri rumahan',
  'mengurus izin penyelenggaraan acara dan kegiatan keramaian',
  'memperbarui data alamat perusahaan pada izin berusaha',
  'mengajukan izin lingkungan untuk pembangunan gudang',
  'menanyakan status penerbitan sertifikat perizinan usaha dagang'],
 'kesehatan': [
  'meminta layanan vaksinasi anak di puskesmas terdekat',
  'mengadukan pelayanan kesehatan pasien di fasilitas puskesmas',
  'mendaftarkan pemeriksaan kesehatan ibu hamil dan layanan posyandu',
  'memohon bantuan pengobatan pasien sakit yang tidak mampu',
  'melaporkan dugaan wabah demam berdarah di lingkungan warga',
  'meminta pemeriksaan sanitasi dan kebersihan air oleh petugas kesehatan',
  'memohon penyuluhan gizi anak dan penanganan stunting',
  'mendapatkan rujukan pemeriksaan medis ke rumah sakit',
  'melaporkan kekurangan obat dan tenaga medis di puskesmas',
  'mengurus jadwal imunisasi serta pemeriksaan penyakit menular']
}
TEMPLATES=[
 'Saya ingin {text}. Mohon informasi persyaratan dan prosesnya.',
 'Mohon bantuan untuk {text} karena saya belum mengetahui tahapannya.',
 'Bagaimana prosedur untuk {text}? Saya membutuhkan arahan petugas.',
 'Saya mengajukan permohonan untuk {text}. Dokumen akan saya lengkapi.',
 'Tolong bantu warga yang perlu {text}, kapan dapat diproses?'
]


if __name__=='__main__':
    path=Path('ml/data/requests.csv');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['text','label','group_id']);writer.writeheader()
        for label,scenarios in SCENARIOS.items():
            for i,text in enumerate(scenarios):
                for template in TEMPLATES:
                    writer.writerow({'text':template.format(text=text),'label':label,'group_id':f'{label}-{i:02d}'})
