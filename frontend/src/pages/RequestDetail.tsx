import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {Button,Dialog,TextArea} from '@radix-ui/themes';
import {ArrowLeft,Brain,ArrowRight} from '@phosphor-icons/react';
import {useData} from '../api/useData';
import {api} from '../api/client';
import type {Agency,RequestItem,Status} from '../api/types';
import {useAuth} from '../auth/AuthProvider';
import {PageState} from '../components/PageState';
import {StatusBadge,statusLabel} from '../components/StatusBadge';
import {RequestTimeline,date} from '../components/RequestTimeline';
import {ServiceFormFields} from '../components/ServiceFormFields';
import {MockChecks} from '../components/MockChecks';
import {WorkflowTasks} from '../components/WorkflowTasks';
import {ClassificationFeedback} from '../components/ClassificationFeedback';
import {RequestAttachments} from '../components/RequestAttachments';
type Confirmation={status:Status;version:number;taskVersion:number};
export function RequestDetail(){
 const {id}=useParams(),{user,decisionDraft,setDecisionDraft}=useAuth();
 const result=useData<RequestItem>('/requests/'+id),agencies=useData<Agency[]>('/agencies');
 const draft=decisionDraft(id??''),{note,target}=draft,additional=draft.additionalTargets??[];
 const setNote=(value:string)=>setDecisionDraft(id??'',{...draft,note:value});
 const setTarget=(value:string)=>setDecisionDraft(id??'',{...draft,target:value,additionalTargets:additional.filter(i=>i!==Number(value))});
 const clearDraft=()=>setDecisionDraft(id??'',{note:'',target:'',additionalTargets:[]});
 const [error,setError]=useState(''),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState<Confirmation|null>(null);
 const item=result.data,ownTask=item?.workflows?.find(t=>t.agency_id===user?.agency_id);
 const final=item?.status==='approved'||item?.status==='rejected'||item?.status==='escalated';
 const actions:Status[]=!item?[]:user?.role==='staff'&&!final?(ownTask?.status==='pending'?['processing','escalated']:ownTask?.status==='processing'?['approved','rejected','escalated']:[]):user?.role==='admin'&&item.status==='escalated'?['approved','rejected']:[];
 async function change(status:Status,snapshot?:Confirmation){
  if(!item)return;setBusy(true);setError('');
  try{
   if(user?.role==='staff'&&ownTask){await api('/requests/'+id+'/tasks/'+ownTask.id,{method:'PATCH',body:JSON.stringify({request_version:snapshot?.version??item.version,task_version:snapshot?.taskVersion??ownTask.version,status,note})})}
   else{await api('/requests/'+id+'/status',{method:'PATCH',body:JSON.stringify({version:snapshot?.version??item.version,status,note})})}
   setConfirm(null);clearDraft();result.reload();
  }catch(exc){setError((exc as Error).message)}finally{setBusy(false)}
 }
 async function reroute(){if(!item)return;setBusy(true);setError('');try{await api('/requests/'+id+'/review-route',{method:'POST',body:JSON.stringify({version:item.version,agency_ids:[Number(target),...additional],note})});clearDraft();result.reload()}catch(exc){setError((exc as Error).message)}finally{setBusy(false)}}
 return <>
  <Link to="/app/requests" className="back-link"><ArrowLeft/>Daftar permohonan</Link><PageState {...result}/>
  {item&&!result.loading&&<>
   <div className="page-heading"><div><span className="eyebrow">{item.reference}</span><h1>{item.title}</h1><p>Diajukan {date(item.created_at)} WIB</p></div><StatusBadge status={item.status}/></div>
   {user?.role==='admin'&&item.classification&&<ClassificationFeedback key={item.id} requestId={item.id}/>}
   <div className="detail-layout"><div>
    <section className="panel"><div className="section-heading"><h2>Kebutuhan yang diajukan</h2></div><p className="request-description">{item.description}</p><div className="detail-meta"><span>Dinas utama<strong>{item.agency_name??'Menunggu pemeriksaan admin'}</strong></span><span>Pembaruan terakhir<strong>{date(item.updated_at)} WIB</strong></span></div></section>
    {item.form&&<section className="panel"><h2>{item.form.title}</h2><p className="subtle">Jawaban formulir versi {item.form.version}</p><ServiceFormFields schema={item.form.schema} answers={item.form.answers} readOnly/></section>}
    {(item.status==='approved'||item.status==='rejected')&&<section className="panel"><h2>Bukti hasil layanan</h2><Link to={'/app/requests/'+id+'/result'}>Lihat bukti hasil</Link></section>}{user?.role!=='citizen'&&<MockChecks key={item.id} requestId={item.id}/>}
    <WorkflowTasks tasks={item.workflows??[]} ownAgency={user?.role==='staff'?user.agency_id:null}/>
    <RequestAttachments requestId={item.id} attachments={item.attachments} workflows={item.workflows} allAgencies={agencies.data??[]} isClosed={item.status==='approved'||item.status==='rejected'} onReload={result.reload}/>
    <section className="panel timeline-panel"><div className="section-heading"><h2>Riwayat permohonan</h2><Button variant="soft" onClick={result.reload}>Muat ulang status</Button></div><RequestTimeline events={item.events}/></section>
    {(actions.length>0||(user?.role==='admin'&&item.status==='escalated'))&&<section className="panel decision-panel">
     <h2>{user?.role==='admin'?'Pemeriksaan akhir admin':'Tindak lanjut petugas'}</h2>{ownTask&&user?.role==='staff'&&<p className="subtle">Keputusan Anda berlaku untuk {ownTask.agency_name}.</p>}
     <label htmlFor="decision-note">Catatan keputusan</label><TextArea id="decision-note" rows={3} maxLength={2000} value={note} disabled={busy} onChange={e=>setNote(e.target.value)} placeholder="Jelaskan keputusan atau alasan pengalihan."/>
     {error&&<p className="error" role="alert">{error}</p>}
     <div className="decision-actions">{actions.map(status=><Button key={status} color={status==='rejected'?'red':status==='escalated'?'amber':'green'} variant={status==='approved'||status==='processing'?'solid':'soft'} disabled={busy||(status!=='processing'&&!note.trim())} onClick={()=>status==='approved'||status==='rejected'?setConfirm({status,version:item.version,taskVersion:ownTask?.version??0}):change(status)}>{status==='processing'?'Mulai proses':status==='escalated'?'Eskalasi':statusLabel[status]}</Button>)}</div>
     {user?.role==='admin'&&item.status==='escalated'&&<div className="reroute-form">
      <label htmlFor="target-agency">Alihkan ke dinas</label><select id="target-agency" value={target} disabled={busy} onChange={e=>setTarget(e.target.value)}><option value="">Pilih dinas utama</option>{agencies.data?.filter(a=>a.active).map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select>
      {target&&<fieldset className="agency-checks"><legend>Dinas pendamping (opsional)</legend>{agencies.data?.filter(a=>a.active&&a.id!==Number(target)).map(a=><label key={a.id}><input type="checkbox" disabled={busy} checked={additional.includes(a.id)} onChange={e=>setDecisionDraft(id??'',{...draft,additionalTargets:e.target.checked?[...additional,a.id]:additional.filter(i=>i!==a.id)})}/>{a.name}</label>)}</fieldset>}
      {agencies.error&&<p className="error" role="alert">{agencies.error}</p>}<Button variant="outline" disabled={busy||!target||!note.trim()} onClick={reroute}>Alihkan permohonan<ArrowRight/></Button>
     </div>}
    </section>}
   </div><aside className="classification-panel"><div className="ml-heading"><Brain size={24}/><span>KLASIFIKASI ML</span></div>{item.classification?<>
    <h2>{item.classification.predicted_agency_code}</h2><span className="confidence">{(item.classification.confidence*100).toFixed(1)}<small>% skor model</small></span><p>{item.classification.needs_review?'Pengajuan awal ditandai untuk pemeriksaan manual.':'ML menentukan kelas utama. Aturan workflow mengatur dinas yang ikut memproses.'}</p>
    <div className="probability-list">{Object.entries(item.classification.probabilities).sort((a,b)=>b[1]-a[1]).map(([label,probability])=><div key={label}><span>{label}</span><strong>{(probability*100).toFixed(1)}%</strong><div style={{width:probability*100+'%'}}/></div>)}</div><small className="model-version">Model: {item.classification.model_version}</small><p className="ml-disclaimer">Skor model bukan jaminan kebenaran. Petugas tetap memutuskan hasil layanan.</p>
   </>:<p>Hasil klasifikasi belum tersedia.</p>}</aside></div>
  </>}
  <Dialog.Root open={confirm!==null} onOpenChange={open=>{if(!open&&!busy)setConfirm(null)}}><Dialog.Content maxWidth="440px"><Dialog.Title>Konfirmasi keputusan</Dialog.Title><Dialog.Description>{user?.role==='staff'?'Keputusan ini berlaku untuk tugas dinas Anda. Penolakan memerlukan review admin; persetujuan menunggu dinas lainnya.':'Admin akan menetapkan keputusan akhir. Keputusan final tidak dapat dibuka ulang pada versi demo ini.'}</Dialog.Description><p>{confirm?statusLabel[confirm.status]:''} — {note}</p>{error&&<p role="alert" className="error">{error}</p>}<div className="dialog-actions"><Button variant="soft" color="gray" disabled={busy} onClick={()=>setConfirm(null)}>Kembali</Button><Button loading={busy} onClick={()=>confirm&&change(confirm.status,confirm)}>Konfirmasi</Button></div></Dialog.Content></Dialog.Root>
 </>;
}
