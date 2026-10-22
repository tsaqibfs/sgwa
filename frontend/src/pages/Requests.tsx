import {useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {Plus,ArrowLeft,ArrowRight,Files} from '@phosphor-icons/react';
import {useAuth} from '../auth/AuthProvider';
import {useData} from '../api/useData';
import {api} from '../api/client';
import type {RequestList,RequestItem,Draft,ServiceForm,FormAnswers} from '../api/types';
import {ServiceFormFields} from '../components/ServiceFormFields';
import {ApiError} from '../api/client';
import {reconcileAnswers} from '../api/formAnswers';
import {RequestForm} from '../components/RequestForm';
import {PageState} from '../components/PageState';
import {StatusBadge} from '../components/StatusBadge';
import {date} from '../components/RequestTimeline';
export function NewRequest(){
 const {draft,setDraft}=useAuth(),navigate=useNavigate(),forms=useData<ServiceForm[]>('/service-forms');
 const [selected,setSelected]=useState<ServiceForm|null>(null),[answers,setAnswers]=useState<FormAnswers>({});
 const [unavailable,setUnavailable]=useState(''),[reviewPending,setReviewPending]=useState(false),[previousAnswers,setPreviousAnswers]=useState<{key:string;label:string;value:string|number|boolean|Record<string,any>}[]>([]);
 async function refreshSelected(){
  if(!selected?.published)return;
  try{
   const next=await api<ServiceForm>('/service-forms/'+selected.id);
   if(!next.published)throw new Error('Formulir belum tersedia.');
   const reconciled=reconcileAnswers(selected.published.schema,next.published.schema,answers);
   setAnswers(reconciled.active);setPreviousAnswers(previous=>[...previous.filter(old=>!reconciled.previous.some(item=>item.key===old.key)),...reconciled.previous]);
   setSelected(next);setUnavailable('');setReviewPending(true);
  }catch{setUnavailable('Formulir belum tersedia untuk dikirim. Jawaban Anda tetap tersimpan. Muat ulang formulir atau pilih layanan lain secara eksplisit.')}
 }
 async function submit(payload:Draft){
  if(unavailable||reviewPending)throw new ApiError(409,unavailable||'Tinjau perubahan formulir sebelum mengirim kembali.');
  const version=selected?.published;
  const submitted=version?{...payload,form_version_id:version.id,form_answers:Object.fromEntries(Object.entries(answers).filter(([key])=>version.schema.fields.some(field=>field.key===key)))}:payload;
  try{const item=await api<RequestItem>('/requests',{method:'POST',body:JSON.stringify(submitted)});setDraft({title:'',description:''});navigate('/app/requests/'+item.id)}
  catch(exc){if(exc instanceof ApiError&&exc.status===409&&selected)await refreshSelected();throw exc}
 }
 function choose(value:string){const form=forms.data?.find(item=>String(item.id)===value)??null;setSelected(form);setUnavailable('');setReviewPending(false);setPreviousAnswers([]);setAnswers(Object.fromEntries((form?.published?.schema.fields??[]).filter(field=>field.type==='checkbox').map(field=>[field.key,false])))}
 return <><Link to="/app/requests" className="back-link"><ArrowLeft/>Permohonan saya</Link><div className="page-heading"><div><span className="eyebrow">PENGAJUAN BARU</span><h1>Apa yang bisa kami bantu?</h1><p>Ceritakan kebutuhan Anda. Sistem akan membantu menentukan dinas tujuan.</p></div></div><div className="submission-layout"><section className="panel form-panel"><div className="service-picker"><label htmlFor="request-service">Layanan opsional</label><select id="request-service" value={selected?.id??''} onChange={e=>choose(e.target.value)}><option value="">Pengajuan teks tanpa formulir</option>{selected&&!forms.data?.some(form=>form.id===selected.id)&&<option value={selected.id}>{selected.title} (belum tersedia)</option>}{forms.data?.map(form=><option key={form.id} value={form.id}>{form.title}</option>)}</select>{forms.error&&<p role="alert" className="error">{forms.error}</p>}<p className="subtle">Pilihan layanan menambahkan isian. ML tetap membantu menentukan kelas utama.</p></div>{unavailable&&<div className="form-review"><p role="alert">{unavailable}</p><Button type="button" variant="outline" onClick={refreshSelected}>Muat ulang formulir</Button></div>}{reviewPending&&<div className="form-review"><p role="status">Formulir berubah. Periksa kembali isian dan jawaban versi sebelumnya.</p>{previousAnswers.map(item=><div key={item.key}><strong>{item.label}</strong><p>{String(item.value)}</p></div>)}<Button type="button" variant="outline" onClick={()=>setReviewPending(false)}>Saya sudah meninjau perubahan formulir</Button></div>}<RequestForm onSubmit={submit} draft={draft} onChange={setDraft}>{selected?.published&&<section><h2>{selected.published.title}</h2><p className="subtle">Formulir versi {selected.published.version}</p><ServiceFormFields schema={selected.published.schema} answers={answers} onChange={setAnswers}/></section>}</RequestForm></section><aside className="submission-guide"><span className="step-chip">SEBELUM MENGIRIM</span><h2>Cerita yang jelas,<br/>arah yang tepat.</h2><p>Sebutkan jenis layanan yang dibutuhkan, kondisi saat ini, dan kendala yang Anda alami.</p><blockquote>“KTP saya hilang. Saya ingin mengurus penggantian dan mengetahui dokumen yang perlu disiapkan.”</blockquote><p className="subtle">Jika formulir dan prediksi ML berbeda, petugas akan meninjau arah layanan.</p></aside></div></>;
}
export function Requests(){const [page,setPage]=useState(1);const result=useData<RequestList>('/requests?page='+page);const {user}=useAuth();return <><div className="page-heading"><div><span className="eyebrow">RUANG LAYANAN</span><h1>{user?.role==='citizen'?'Permohonan saya':'Antrean permohonan'}</h1><p>Setiap pengajuan, satu riwayat yang jelas.</p></div>{user?.role==='citizen'&&<Button asChild size="3"><Link to="/app/requests/new"><Plus/>Pengajuan baru</Link></Button>}</div><section className="panel"><div className="section-heading"><h2>Daftar permohonan</h2><Button variant="soft" onClick={result.reload}>Muat ulang</Button></div><PageState {...result}/>{result.data&&!result.loading&&(result.data.items.length?<><div className="request-rows">{result.data.items.map(item=><Link key={item.id} to={'/app/requests/'+item.id} className="request-row"><Files className="row-file" size={24}/><div className="request-row-main"><small>{item.reference}</small><strong>{item.title}</strong><span>{item.agency_name??'Review admin'} · {date(item.created_at)}</span></div><StatusBadge status={item.status}/><ArrowRight className="row-arrow"/></Link>)}</div><div className="pagination"><span>{result.data.total} permohonan · halaman {page}</span><Button variant="outline" disabled={page===1} onClick={()=>setPage(n=>n-1)}>Sebelumnya</Button><Button variant="outline" disabled={page*20>=result.data.total} onClick={()=>setPage(n=>n+1)}>Berikutnya</Button></div></>:<div className="empty"><Files size={36}/><h3>Belum ada permohonan</h3><p>Permohonan yang tersedia akan ditampilkan di sini.</p></div>)}</section></>}
