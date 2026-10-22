import {useRef,useState} from 'react';
import {Button,TextArea,TextField} from '@radix-ui/themes';
import {api,ApiError} from '../api/client';
import {useData} from '../api/useData';
import type {FeedbackList,MLLabel} from '../api/ml';
import {PageState} from './PageState';

export function ClassificationFeedback({requestId}:{requestId:number}){
 const labels=useData<MLLabel[]>('/ml/labels'),history=useData<FeedbackList>(`/ml/feedback?request_id=${requestId}&page_size=100`);
 const [target,setTarget]=useState(''),[text,setText]=useState(''),[provenance,setProvenance]=useState(''),[reason,setReason]=useState(''),[family,setFamily]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[conflict,setConflict]=useState(false);
 const attempt=useRef<{signature:string;key:string}|null>(null);
 const revision=history.data?.items[0]?.current_revision??0;
 async function save(event:React.FormEvent){
  event.preventDefault();if(busy||conflict)return;setBusy(true);setError('');setMessage('');
  const values={expected_revision:revision,training_text:text.trim(),corrected_code:target,provenance,reason:reason.trim(),family_key:family.trim()||null};
  const signature=JSON.stringify(values);if(attempt.current?.signature!==signature)attempt.current={signature,key:crypto.randomUUID()};
  try{await api(`/ml/requests/${requestId}/feedback`,{method:'POST',body:JSON.stringify({...values,idempotency_key:attempt.current.key})});attempt.current=null;history.reload();setMessage('Koreksi tersimpan dan menunggu verifikasi admin.');}
  catch(exc){setError((exc as Error).message);if(exc instanceof ApiError&&exc.status===409){setConflict(true);history.reload();}}
  finally{setBusy(false)}
 }
 const valid=target&&provenance&&text.trim().length>=10&&reason.trim().length>=3;
 return <section className="panel ml-feedback-panel"><h2>Koreksi klasifikasi untuk training</h2><p>Koreksi ini tidak mengubah dinas tujuan, keputusan layanan, atau prediksi awal. Verifikasi sebelum digunakan untuk training.</p>
  <PageState {...labels}/><PageState {...history}/>
  <form onSubmit={save} className="ml-feedback-form"><fieldset disabled={busy||labels.loading||history.loading||!!labels.error||!!history.error}>
   <label htmlFor={`ml-label-${requestId}`}>Kelas utama yang benar</label><select id={`ml-label-${requestId}`} value={target} onChange={e=>setTarget(e.target.value)} required><option value="">Pilih kelas</option>{labels.data?.map(label=><option key={label.code} value={label.code} disabled={!label.active}>{label.name}{!label.active?' (nonaktif)':''}</option>)}</select>
   <label htmlFor={`ml-text-${requestId}`}>Teks training yang sudah disunting</label><TextArea id={`ml-text-${requestId}`} value={text} onChange={e=>setText(e.target.value)} rows={4} minLength={10} maxLength={5000} required/><small>Hapus NIK, nomor telepon, alamat pribadi, dan identitas lain. Teks asli tetap tersimpan dalam riwayat permohonan.</small>
   <label htmlFor={`ml-source-${requestId}`}>Asal data</label><select id={`ml-source-${requestId}`} required value={provenance} onChange={e=>setProvenance(e.target.value)}><option value="">Pilih secara eksplisit</option><option value="synthetic_demo">Sintetis / demonstrasi</option><option value="real">Permohonan nyata yang sudah disunting</option></select>
   <label htmlFor={`ml-reason-${requestId}`}>Alasan koreksi</label><TextArea id={`ml-reason-${requestId}`} value={reason} onChange={e=>setReason(e.target.value)} minLength={3} maxLength={1000} required/>
   <label htmlFor={`ml-family-${requestId}`}>Kode keluarga skenario (opsional)</label><TextField.Root id={`ml-family-${requestId}`} value={family} onChange={e=>setFamily(e.target.value)} maxLength={80} pattern="[a-z0-9_-]+"/><small>Gunakan kode sama untuk parafrasa satu skenario agar tidak bocor antar-fold.</small>
   <Button type="submit" disabled={!valid||conflict} loading={busy}>Simpan koreksi</Button>
  </fieldset></form>
  {error&&<p className="error" role="alert">{error}</p>}{message&&<p role="status">{message}</p>}
  {conflict&&<><p>Teks Anda tetap tersimpan. Periksa revisi terbaru sebelum mencoba lagi.</p><Button variant="soft" disabled={history.loading||!!history.error||!history.data} onClick={()=>{setConflict(false);attempt.current=null;setError('')}}>Saya sudah meninjau revisi terbaru</Button></>}
  <h3>Riwayat koreksi</h3>{history.data?.items.length===0&&<p>Belum ada koreksi.</p>}{history.data?.items.map(row=><details key={row.id}><summary>Revisi {row.revision} · {row.status} · {row.corrected_code}</summary><p>{row.training_text}</p><p>Asal: {row.provenance} · {row.reason}</p>{row.review_note&&<p>Verifikasi: {row.review_note}</p>}</details>)}
 </section>;
}
