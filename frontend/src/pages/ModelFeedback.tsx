import {useState} from 'react';
import {Link} from 'react-router-dom';
import {Button,TextArea} from '@radix-ui/themes';
import {useData} from '../api/useData';
import {api} from '../api/client';
import type {Feedback,FeedbackList,MLLabel} from '../api/ml';
import {PageState} from '../components/PageState';

function FeedbackReview({row,reload}:{row:Feedback;reload:()=>void}){
 const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function review(decision:'verified'|'rejected'){
  if(busy)return;setBusy(true);setError('');
  try{await api(`/ml/feedback/${row.id}/review`,{method:'POST',body:JSON.stringify({expected_revision:row.current_revision,decision,note:note.trim()})});reload()}
  catch(exc){setError((exc as Error).message);reload()}finally{setBusy(false)}
 }
 return <><label htmlFor={'review-'+row.id}>Catatan verifikasi</label><TextArea id={'review-'+row.id} value={note} onChange={e=>setNote(e.target.value)} minLength={3} maxLength={1000} disabled={busy}/>
 <div className="ml-actions"><Button disabled={note.trim().length<3||busy} onClick={()=>review('verified')}>Verifikasi koreksi</Button><Button variant="soft" color="red" disabled={note.trim().length<3||busy} onClick={()=>review('rejected')}>Tolak koreksi</Button></div>{error&&<p role="alert" className="error">{error}</p>}</>;
}

export function ModelFeedback(){
 const [status,setStatus]=useState(''),[source,setSource]=useState(''),[page,setPage]=useState(1);
 const result=useData<FeedbackList>(`/ml/feedback?page=${page}&page_size=20${status?'&status='+status:''}${source?'&provenance='+source:''}`),labels=useData<MLLabel[]>('/ml/labels');
 const names=Object.fromEntries(labels.data?.map(l=>[l.code,l.name])??[]);
 return <><div className="page-heading"><div><span className="eyebrow">PEMBELAJARAN DARI KOREKSI</span><h1>Feedback klasifikasi</h1><p>Hanya revisi terkini yang telah diverifikasi menjadi bahan training. Pengalihan dinas tidak otomatis menjadi label ML.</p></div></div>
 <section className="panel"><div className="ml-filters"><label>Status<select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}><option value="">Semua</option>{['pending','verified','rejected','superseded'].map(s=><option key={s}>{s}</option>)}</select></label><label>Asal data<select value={source} onChange={e=>{setSource(e.target.value);setPage(1)}}><option value="">Semua</option><option value="synthetic_demo">Sintetis / demo</option><option value="real">Nyata, sudah disunting</option></select></label></div>
 <PageState {...result}/>{result.data?.items.length===0&&<p>Belum ada feedback sesuai filter.</p>}
 {result.data?.items.map(row=><article className="ml-feedback-entry" key={row.id}><div className="section-heading"><h2>{names[row.corrected_code]??row.corrected_code}</h2><span>{row.status} · revisi {row.revision}</span></div><Link to={'/app/requests/'+row.request_id}>Buka permohonan #{row.request_id}</Link><p>{row.training_text}</p><p className="subtle">{row.provenance==='real'?'Data nyata tersunting':'Data sintetis/demo'} · {row.reason}</p><details><summary>Prediksi awal dan catatan</summary><p>{row.original_prediction.predicted_agency_code} · {row.original_prediction.model_version}</p><p>{row.review_note??'Belum diverifikasi.'}</p></details>{row.is_current&&row.status==='pending'&&<FeedbackReview row={row} reload={result.reload}/>}</article>)}
 <div className="ml-actions"><Button variant="soft" disabled={page===1||result.loading} onClick={()=>setPage(p=>p-1)}>Sebelumnya</Button><span>Halaman {page} · {result.data?.total??0} koreksi</span><Button variant="soft" disabled={!result.data||page*20>=result.data.total||result.loading} onClick={()=>setPage(p=>p+1)}>Berikutnya</Button></div>
 </section><section className="panel"><h2>Training ulang secara batch</h2><p>Operator menjalankan training setelah koreksi diverifikasi. Kandidat perlu dievaluasi dan diaktifkan admin melalui <Link to="/app/model">halaman model</Link>.</p><p>Native, dari root proyek:</p><pre className="ml-command">{'.\\.venv\\Scripts\\python.exe -m scripts.train_candidate --actor-email admin@demo.sgwa.id'}</pre><p>Docker:</p><pre className="ml-command">{'docker compose --env-file .env.docker -f compose.docker.yaml run --rm init python -m scripts.train_candidate --actor-email admin@demo.sgwa.id'}</pre><p>Training tidak menjamin skor meningkat dan tidak mengganti model aktif secara otomatis.</p></section></>;
}
