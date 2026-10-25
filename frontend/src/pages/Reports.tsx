import {useRef,useState} from 'react';
import {Link} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {DownloadSimple} from '@phosphor-icons/react';
import {useAuth} from '../auth/AuthProvider';
import {useData} from '../api/useData';
import {apiFile} from '../api/client';
import {defaultReportFilters,reportSearch,saveReportFile,type ReportFilterDraft,type ReportResponse} from '../api/reports';
import type {Agency,Status} from '../api/types';
import {StatusBadge,statusLabel} from '../components/StatusBadge';
import {PageState} from '../components/PageState';
import {date} from '../components/RequestTimeline';

export function Reports(){
 const {user}=useAuth();
 const showClassification=user?.role==='admin';
 const defaults=():ReportFilterDraft=>({...defaultReportFilters(new Date()),agency_id:user?.role==='staff'&&user.agency_id?String(user.agency_id):''});
 const [draft,setDraft]=useState(defaults),[applied,setApplied]=useState(defaults),[page,setPage]=useState(1),[busy,setBusy]=useState(false),[downloadError,setDownloadError]=useState('');
 const lock=useRef(false),result=useData<ReportResponse>('/reports?'+reportSearch(applied,page)),agencies=useData<Agency[]>('/agencies');
 const data=result.data;
 const matching=!!data&&data.page===page&&data.filters.date_from===(applied.date_from||null)&&data.filters.date_to===(applied.date_to||null)&&data.filters.status===(applied.status||null)&&data.filters.agency_id===(applied.agency_id?Number(applied.agency_id):null);
 const canDownload=matching&&!result.fetching&&!result.error&&!busy;
 function edit(key:keyof ReportFilterDraft,value:string){setDraft(old=>({...old,[key]:value}))}
 function apply(event:React.FormEvent){event.preventDefault();if(lock.current)return;setApplied({...draft});setPage(1);setDownloadError('');result.reload()}
 function reset(){if(lock.current)return;const next=defaults();setDraft(next);setApplied(next);setPage(1);setDownloadError('');result.reload()}
 async function download(){
  if(!canDownload||lock.current)return;lock.current=true;setBusy(true);setDownloadError('');
  try{saveReportFile(await apiFile('/reports/requests.csv?'+reportSearch(applied)))}
  catch(exc){setDownloadError((exc as Error).message)}finally{lock.current=false;setBusy(false)}
 }
 const summary=matching?data!.summary:null;
 return <><div className="page-heading"><div><span className="eyebrow">DATA LAYANAN DALAM CAKUPAN ANDA</span><h1>Laporan layanan</h1><p>Ringkasan dan ekspor permohonan sesuai hak akses. Tanggal pengajuan memakai WIB.</p></div><Button disabled={!canDownload} loading={busy} onClick={download}><DownloadSimple/>Unduh CSV</Button></div>
 <section className="panel report-filters"><h2>Filter laporan</h2><form onSubmit={apply}><fieldset disabled={busy}><div className="report-filter-grid">
  <label>Tanggal awal (WIB)<input type="date" value={draft.date_from} onChange={e=>edit('date_from',e.target.value)}/></label><label>Tanggal akhir (WIB)<input type="date" value={draft.date_to} onChange={e=>edit('date_to',e.target.value)}/></label>
  <label>Status permohonan<select value={draft.status} onChange={e=>edit('status',e.target.value)}><option value="">Semua status</option>{Object.entries(statusLabel).map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label>
  <label>Dinas dalam laporan<select value={draft.agency_id} disabled={user?.role==='staff'||agencies.loading} onChange={e=>edit('agency_id',e.target.value)}><option value="">{user?.role==='staff'?'Belum ditugaskan ke dinas':'Semua dinas'}</option>{agencies.data?.map(agency=><option value={agency.id} key={agency.id}>{agency.name}{!agency.active?' (nonaktif)':''}</option>)}</select></label>
 </div><div className="report-actions"><Button type="submit">Terapkan filter</Button><Button type="button" variant="soft" onClick={reset}>Reset</Button></div></fieldset></form>{agencies.error&&<p role="alert" className="error">Daftar dinas: {agencies.error}</p>}<p className="subtle">Filter dinas mencakup dinas utama dan pendamping. Pengubahan isian berlaku setelah Terapkan filter. CSV maksimal 5.000 permohonan.</p></section>
 {downloadError&&<p role="alert" className="error">{downloadError}</p>}<PageState loading={result.loading||(!matching&&!result.error)} error={result.error} reload={result.reload}/>
 {summary&&<><div className="report-metrics"><section className="panel"><span>Total permohonan</span><strong>{summary.total.toLocaleString('id-ID')}</strong></section><section className="panel"><span>Keputusan final</span><strong>{summary.completed_count.toLocaleString('id-ID')}</strong></section><section className="panel"><span>Tingkat penyelesaian</span><strong>{summary.completion_rate===null?'—':(summary.completion_rate*100).toLocaleString('id-ID',{maximumFractionDigits:1})+'%'}</strong></section><section className="panel"><span>Rata-rata durasi final</span><strong>{summary.average_completed_hours===null?'—':summary.average_completed_hours.toLocaleString('id-ID',{maximumFractionDigits:1})+' jam'}</strong></section></div>
 <section className="panel report-summary"><h2>Ringkasan status</h2><div className="report-statuses">{Object.entries(summary.by_status).map(([status,count])=><div key={status}><StatusBadge status={status as Status}/><strong>{count.toLocaleString('id-ID')}</strong></div>)}</div><p>Permohonan dengan tugas melewati SLA dalam cakupan laporan: <strong>{summary.overdue_count}</strong></p><p className="subtle">Selesai mencakup disetujui dan ditolak. Durasi dihitung dari pengajuan sampai timestamp keputusan final yang tersimpan, bukan waktu aktif petugas.</p></section>
 <section className="panel report-table"><div className="section-heading"><h2>Permohonan dalam laporan</h2><Button variant="soft" disabled={busy||result.fetching} onClick={result.reload}>Muat ulang</Button></div>{result.fetching&&<p role="status">Menyegarkan laporan…</p>}<p className="subtle">Disusun {date(data!.generated_at)} · {data!.total} permohonan. CSV dibuat dari snapshot terbaru saat diunduh.</p>
 {data!.items.length===0?<p>Tidak ada permohonan sesuai filter.</p>:<div className="table-scroll"><table><thead><tr><th>Permohonan</th><th>Status</th><th>Dinas utama / terlibat</th><th>Diajukan (WIB)</th>{showClassification&&<th>Prediksi ML historis</th>}</tr></thead><tbody>{data!.items.map(row=><tr key={row.id}><td><Link to={'/app/requests/'+row.id}>{row.reference}</Link><p>{row.title}</p></td><td><StatusBadge status={row.status}/></td><td>{row.primary_agency?.name??'Belum ditugaskan'}<p className="subtle">{row.agencies.map(a=>a.name).join('; ')||'Belum ada tugas dinas'}</p></td><td>{date(row.created_at)}</td>{showClassification&&<td>{row.classification?<><strong>{row.classification.predicted_agency_code}</strong><p>Confidence {(row.classification.confidence*100).toLocaleString('id-ID',{maximumFractionDigits:1})}%</p><small className="model-id">{row.classification.model_version}</small></>:'—'}</td>}</tr>)}</tbody></table></div>}
 <p className="subtle">{showClassification&&'Confidence ML bukan ukuran akurasi atau keputusan layanan. '}Identitas pemohon, deskripsi dan jawaban formulir tidak dimasukkan ke CSV.</p><div className="pagination"><span>Halaman {page} · {data!.total} permohonan</span><Button variant="outline" disabled={page===1||busy||result.fetching} onClick={()=>setPage(n=>n-1)}>Sebelumnya</Button><Button variant="outline" disabled={page*data!.page_size>=data!.total||busy||result.fetching} onClick={()=>setPage(n=>n+1)}>Berikutnya</Button></div></section></>}
 </>;
}
