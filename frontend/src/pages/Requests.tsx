import {useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {Plus,ArrowLeft,ArrowRight,Files} from '@phosphor-icons/react';
import {useAuth} from '../auth/AuthProvider';
import {useData} from '../api/useData';
import {api} from '../api/client';
import type {RequestList,RequestItem,Draft} from '../api/types';
import {RequestForm} from '../components/RequestForm';
import {PageState} from '../components/PageState';
import {StatusBadge} from '../components/StatusBadge';
import {date} from '../components/RequestTimeline';
export function NewRequest(){
 const {draft,setDraft}=useAuth(),navigate=useNavigate();
 async function submit(payload:Draft){
  const item=await api<RequestItem>('/requests',{method:'POST',body:JSON.stringify(payload)});
  setDraft({title:'',description:''});navigate('/app/requests/'+item.id);
 }
 return <><Link to="/app/requests" className="back-link"><ArrowLeft/>Permohonan saya</Link><div className="page-heading"><div><span className="eyebrow">PENGAJUAN BARU</span><h1>Apa yang bisa kami bantu?</h1><p>Ceritakan kebutuhan Anda. Sistem akan membantu menentukan dinas tujuan.</p></div></div><div className="submission-layout"><section className="panel form-panel"><RequestForm onSubmit={submit} draft={draft} onChange={setDraft}/></section><aside className="submission-guide"><span className="step-chip">SEBELUM MENGIRIM</span><h2>Cerita yang jelas,<br/>arah yang tepat.</h2><p>Sebutkan jenis layanan yang dibutuhkan, kondisi saat ini, dan kendala yang Anda alami.</p><blockquote>“KTP saya hilang. Saya ingin mengurus penggantian dan mengetahui dokumen yang perlu disiapkan.”</blockquote></aside></div></>;
}
export function Requests(){const [page,setPage]=useState(1);const result=useData<RequestList>('/requests?page='+page);const {user}=useAuth();return <><div className="page-heading"><div><span className="eyebrow">RUANG LAYANAN</span><h1>{user?.role==='citizen'?'Permohonan saya':'Antrean permohonan'}</h1><p>Setiap pengajuan, satu riwayat yang jelas.</p></div>{user?.role==='citizen'&&<Button asChild size="3"><Link to="/app/requests/new"><Plus/>Pengajuan baru</Link></Button>}</div><section className="panel"><div className="section-heading"><h2>Daftar permohonan</h2><Button variant="soft" onClick={result.reload}>Muat ulang</Button></div><PageState {...result}/>{result.data&&!result.loading&&(result.data.items.length?<><div className="request-rows">{result.data.items.map(item=><Link key={item.id} to={'/app/requests/'+item.id} className="request-row"><Files className="row-file" size={24}/><div className="request-row-main"><small>{item.reference}</small><strong>{item.title}</strong><span>{item.agency_name??'Review admin'} · {date(item.created_at)}</span></div><StatusBadge status={item.status}/><ArrowRight className="row-arrow"/></Link>)}</div><div className="pagination"><span>{result.data.total} permohonan · halaman {page}</span><Button variant="outline" disabled={page===1} onClick={()=>setPage(n=>n-1)}>Sebelumnya</Button><Button variant="outline" disabled={page*20>=result.data.total} onClick={()=>setPage(n=>n+1)}>Berikutnya</Button></div></>:<div className="empty"><Files size={36}/><h3>Belum ada permohonan</h3><p>Permohonan yang tersedia akan ditampilkan di sini.</p></div>)}</section></>}
