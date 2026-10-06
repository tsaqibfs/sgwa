import {useEffect,useState,type FormEvent} from 'react';
import {Button} from '@radix-ui/themes';
import {useData} from '../api/useData';
import {api} from '../api/client';
import type {Agency} from '../api/types';
import {PageState} from '../components/PageState';
type Rule={source_code:string;source_name:string;active:boolean;agency_ids:number[]};
export function WorkflowRoutes(){
 const rules=useData<Rule[]>('/workflow/routes'),agencies=useData<Agency[]>('/agencies');
 const [source,setSource]=useState(''),[selected,setSelected]=useState<number[]>([]),[dirty,setDirty]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
 useEffect(()=>{if(!source&&rules.data?.length)setSource(rules.data.find(r=>r.active)?.source_code??'')},[rules.data,source]);
 useEffect(()=>{if(!dirty)setSelected(rules.data?.find(r=>r.source_code===source)?.agency_ids??[])},[source,rules.data,dirty]);
 const primary=agencies.data?.find(a=>a.code===source);
 async function save(e:FormEvent){e.preventDefault();if(busy)return;setBusy(true);setError('');setMessage('');try{await api('/workflow/routes/'+encodeURIComponent(source),{method:'PUT',body:JSON.stringify({agency_ids:selected})});setMessage('Rute tersimpan.');rules.reload()}catch(exc){setError((exc as Error).message)}finally{setBusy(false)}}
 return <><div className="page-heading"><div><span className="eyebrow">KOORDINASI DINAS</span><h1>Aturan routing layanan</h1><p>Model AI memilih satu kelas utama. Aturan ini menentukan dinas yang bekerja bersama untuk pengajuan baru.</p></div></div><section className="panel routing-panel"><PageState {...rules}/><PageState {...agencies}/>{rules.data&&agencies.data&&<form onSubmit={save}><label htmlFor="route-source">Kelas utama</label><select id="route-source" value={source} disabled={busy} onChange={e=>{setDirty(false);setSource(e.target.value);setMessage('');setError('')}}>{rules.data.filter(r=>r.active).map(r=><option key={r.source_code} value={r.source_code}>{r.source_name} ({r.source_code})</option>)}</select><fieldset disabled={busy}><legend>Dinas tujuan</legend><p className="subtle">Dinas utama selalu ikut. Semua dinas harus menyetujui sebelum permohonan selesai.</p>{agencies.data.filter(a=>a.active).map(a=><label className="destination-choice" key={a.id}><input type="checkbox" checked={selected.includes(a.id)} disabled={a.id===primary?.id} onChange={e=>{setDirty(true);setMessage('');setSelected(ids=>e.target.checked?[...ids,a.id]:ids.filter(id=>id!==a.id))}}/><span>{a.name}</span>{a.id===primary?.id&&<small>Utama</small>}</label>)}</fieldset>{error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}<Button type="submit" disabled={!source||selected.length===0||selected.length>20} loading={busy}>Simpan rute</Button><p className="subtle">Maksimal 20 dinas. Perubahan tidak mengubah tugas permohonan yang sudah dibuat.</p></form>}</section></>;
}
