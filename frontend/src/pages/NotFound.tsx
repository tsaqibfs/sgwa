import {Link} from 'react-router-dom';
import {ArrowLeft,Buildings} from '@phosphor-icons/react';
export function NotFound(){return <main id="main-content" tabIndex={-1} className="not-found"><span className="brand-icon"><Buildings size={28}/></span><span className="not-found-number" aria-hidden="true">404</span><span className="eyebrow">Alamat belum ditemukan</span><h1>Halaman tidak ditemukan</h1><p>Alamat ini mungkin salah atau sudah berubah. Kembali ke beranda untuk melanjutkan layanan.</p><Link to="/" className="return-home"><ArrowLeft size={20}/>Kembali ke beranda</Link></main>}
