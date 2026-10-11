import {useState} from 'react';
import {Button,TextArea} from '@radix-ui/themes';
import {api,ApiError} from '../api/client';
import {useData} from '../api/useData';
import type {ModelReport,ModelVersionsResponse} from '../api/ml';
import {PageState} from './PageState';

export function ModelVersions(){
 const result=useData<ModelVersionsResponse>('/ml/versions');
 const [reason,setReason]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[candidate,setCandidate]=useState<ModelReport|null>(null),[reviewed,setReviewed]=useState('');
 async function inspect(id:string){setBusy(true);setError('');setCandidate(null);setReviewed('');try{const report=await api<ModelReport>(`/ml/versions/${id}/evaluation`);setCandidate(report);setReviewed(id)}catch(exc){setError((exc as Error).message)}finally{setBusy(false)}}
 async function change(id:string,kind:'activate'|'rollback'){
  if(!result.data||busy)return;setBusy(true);setError('');setMessage('');
  try{await api(`/ml/versions/${id}/${kind}`,{method:'POST',body:JSON.stringify({expected_revision:result.data.revision,reason:reason.trim()})});setMessage(kind==='rollback'?'Rollback berhasil.':'Model diaktifkan.');setReason('');setReviewed('');setCandidate(null);window.dispatchEvent(new Event('sgwa:data-changed'));result.reload()}
  catch(exc){setError((exc as Error).message);if(exc instanceof ApiError&&exc.status===409){setReviewed('');setCandidate(null);result.reload()}}finally{setBusy(false)}
 }
 return <section className="panel model-versions"><h2>Versi model & aktivasi</h2><p>Kandidat tidak otomatis aktif. Periksa evaluasi sebelum aktivasi; prediksi historis tetap memakai versi semula.</p><PageState {...result}/>{result.data&&<><p>Model aktif: <strong className="model-id">{result.data.active_model_id??'Belum ada'}</strong></p><label htmlFor="model-change-reason">Alasan aktivasi / rollback</label><TextArea id="model-change-reason" value={reason} onChange={e=>setReason(e.target.value)} maxLength={1000} disabled={busy}/>
 {result.data.items.map(row=><article className="ml-feedback-entry" key={row.id}><h3 className="model-id">{row.id}</h3><p>{row.id===result.data!.active_model_id?'AKTIF':row.state==='failed'?'TRAINING GAGAL':'KANDIDAT'} · Macro-F1 {row.macro_f1?.toFixed(3)??'—'}</p>{row.below_target&&row.state==='ready'&&<p className="ml-warning">Di bawah target proyek 0,85. Nilai berasal dari holdout sintetis.</p>}{row.reason&&<p className="subtle">{row.reason}</p>}<div className="ml-actions"><Button variant="soft" disabled={busy||row.state!=='ready'} onClick={()=>inspect(row.id)}>Lihat evaluasi</Button><Button disabled={busy||!row.can_activate||reviewed!==row.id||reason.trim().length<3||row.id===result.data!.active_model_id} onClick={()=>change(row.id,'activate')}>Aktifkan</Button>{row.ever_active&&row.id!==result.data!.active_model_id&&<Button variant="outline" disabled={busy||reviewed!==row.id||reason.trim().length<3} onClick={()=>change(row.id,'rollback')}>Rollback</Button>}</div></article>)}</>}
 {candidate&&<div className="model-notice"><h3>Evaluasi pada holdout sintetis</h3><p className="model-id">{candidate.model_version}</p><p>Macro-F1 {candidate.macro_f1.toFixed(3)} · CV {candidate.cross_validation.mean_macro_f1.toFixed(3)} ± {candidate.cross_validation.std_macro_f1.toFixed(3)}</p><p>Threshold {(candidate.routing_policy.threshold*100).toFixed(0)}% · routing otomatis {candidate.routing_policy.auto_routing_enabled?'aktif':'nonaktif'} · coverage validasi {(candidate.routing_policy.coverage*100).toFixed(1)}%</p><p>Asal training: {Object.entries(candidate.provenance_counts).map(([key,n])=>`${key}: ${n}`).join(', ')}</p><details><summary>Recall setiap kelas</summary>{candidate.classes.map(code=><p key={code}>{code}: {candidate.classification_report[code].recall.toFixed(3)}</p>)}</details></div>}
 {error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}</section>;
}
