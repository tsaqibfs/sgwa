import {Link} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {Buildings,ArrowUpRight,ArrowRight,FileText,GitBranch,CheckCircle,ShieldCheck} from '@phosphor-icons/react';
import {useAuth} from '../auth/AuthProvider';
export function Home(){
 const {user}=useAuth();
 return <div className="home">
  <header className="home-nav"><Link to="/" className="brand"><span className="brand-icon"><Buildings size={26} weight="bold"/></span><span>SGWA<small>LAYANAN PUBLIK</small></span></Link><div><a href="#cara-kerja">Cara kerja</a><Button asChild variant="outline"><Link to={user?'/app':'/login'}>{user?'Ruang kerja':'Masuk'}<ArrowUpRight/></Link></Button></div></header>
  <main id="main-content" tabIndex={-1}>
   <section className="home-hero">
    <div className="hero-copy"><span className="eyebrow"><span className="green-dot"/> Ruang layanan warga</span><h1>Kebutuhan Anda.<br/>Dinas yang tepat.<br/><em>Proses yang jelas.</em></h1><p>Mulai dari satu cerita. Sampaikan kebutuhan Anda, temukan dinas tujuan, dan ikuti prosesnya hingga ada keputusan.</p><div className="hero-actions"><Button size="4" asChild><Link to={user?'/app/requests/new':'/register'}>Ajukan permohonan<ArrowRight/></Link></Button><a href="#cara-kerja">Kenali alurnya<ArrowUpRight size={17}/></a></div><div className="hero-trust"><ShieldCheck size={20}/> Teknologi membantu. Petugas memutuskan.</div></div>
    <figure className="routing-map" aria-label="Alur pengajuan: cerita warga diklasifikasikan ML, lalu diarahkan ke dinas atau diperiksa admin.">
     <figcaption><span>Contoh perjalanan layanan</span><span className="map-index">01 — 03</span></figcaption>
     <div className="map-submission"><span className="map-icon"><FileText size={25}/></span><div><small>01 / PENGAJUAN</small><strong>Dimulai dari cerita Anda</strong><p>Kebutuhan ditulis dengan bahasa sehari-hari.</p></div></div>
     <div className="map-connector" aria-hidden="true"/>
     <div className="map-classifier"><GitBranch size={31}/><div><small>02 / KLASIFIKASI TEKS</small><strong>Sistem menemukan arah</strong></div><span className="map-ml">ML</span></div>
     <div className="map-branches" aria-hidden="true"><span/><span/><span/></div>
     <div className="map-destinations"><span><Buildings size={23}/>Dukcapil</span><span><ShieldCheck size={23}/>Perizinan</span><span><CheckCircle size={23}/>Pajak</span></div>
     <div className="map-review"><span className="green-dot"/><p>Belum jelas? Admin memeriksa pengajuan sebelum menentukan dinas.</p></div>
     <div className="map-caption"><span>03 / TINDAK LANJUT</span><strong>Petugas menindaklanjuti.</strong></div>
    </figure>
   </section>
   <section id="cara-kerja" className="home-detail">
    <div className="detail-intro"><span className="eyebrow">Dari pengajuan ke keputusan</span><h2>Layanan yang<br/>bisa Anda ikuti.</h2><p>Satu ruang untuk mengajukan kebutuhan dan melihat perkembangannya.</p></div>
    <ol className="home-steps"><li><span>01</span><div><h3>Ceritakan kebutuhan</h3><p>Tulis judul dan penjelasan singkat. Anda tidak perlu memilih dinas sendiri.</p></div><FileText size={23}/></li><li><span>02</span><div><h3>Temukan dinas tujuan</h3><p>ML menyarankan rute. Pengajuan yang belum jelas masuk ke pemeriksaan admin.</p></div><GitBranch size={23}/></li><li><span>03</span><div><h3>Pantau tindak lanjut</h3><p>Lihat status, catatan petugas, dan riwayat keputusan dalam satu permohonan.</p></div><CheckCircle size={23}/></li></ol>
    <div className="academic-note"><strong>Demonstrasi akademik</strong><span>SGWA menggunakan data fiktif dan model yang dilatih pada teks sintetis. Portal ini belum terhubung dengan layanan pemerintah.</span></div>
   </section>
  </main>
  <footer className="home-footer"><span><strong>SGWA</strong> · Smart Government Workflow Automation</span><span>Dari kebutuhan, menuju layanan.</span></footer>
 </div>;
}
