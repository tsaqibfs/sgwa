import {useRef,useState} from 'react';
import {Button} from '@radix-ui/themes';
import {api} from '../api/client';
import {useData} from '../api/useData';
import {PageState} from './PageState';
import {date} from './RequestTimeline';
import type {MockCheck} from '../api/types';

export function MockChecks({requestId}:{requestId:number}){
 const history=useData<MockCheck[]>('/requests/'+requestId+'/mock-checks');
 const [type,setType]=useState('identity'),[scenario,setScenario]=useState('success'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const retry=useRef<{signature:string;key:string}|null>(null);
 async function run(){if(busy)return;setBusy(true);setError('');const signature=[requestId,type,scenario].join(':');if(retry.current?.signature!==signature)retry.current={signature,key:crypto.randomUUID()};try{await api('/requests/'+requestId+'/mock-checks',{method:'POST',body:JSON.stringify({check_type:type,scenario,idempotency_key:retry.current.key})});retry.current=null;history.reload()}catch(exc){setError((exc as Error).message)}finally{setBusy(false)}}
 return <section className="panel mock-panel"><span className="eyebrow">SIMULASI API</span><h2>Simulasi pemeriksaan</h2><p className="subtle">Menggunakan fixture sintetis lokal. Hasil menjadi informasi untuk petugas; keputusan tetap dilakukan secara manual.</p><div className="mock-controls"><label>Jenis pemeriksaan<select disabled={busy} value={type} onChange={e=>{setType(e.target.value);retry.current=null}}><option value="identity">Identitas</option><option value="permit_completeness">Kelengkapan izin</option><option value="general_service">Layanan umum</option></select></label><label>Skenario simulasi<select disabled={busy} value={scenario} onChange={e=>{setScenario(e.target.value);retry.current=null}}><option value="success">Cocok</option><option value="mismatch">Tidak cocok</option><option value="unavailable">Tidak tersedia</option></select></label><Button loading={busy} onClick={run}>Jalankan simulasi</Button></div>{error&&<p role="alert" className="error">{error}</p>}<PageState {...history}/><div className="mock-history">{history.data?.map(check=><article key={check.id}><strong>{check.payload.subject}</strong><span className="demo-pill">SIMULASI</span><p>{check.payload.message}</p><small>{check.check_type} · <span>{check.outcome}</span> · {date(check.checked_at)} WIB · {check.payload.fixture}</small></article>)}{history.data?.length===0&&<p className="subtle">Belum ada pemeriksaan simulasi.</p>}</div></section>;
}
