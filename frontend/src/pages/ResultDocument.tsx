import {Link,useParams} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {useData} from '../api/useData';
import {PageState} from '../components/PageState';
import {date} from '../components/RequestTimeline';
import {statusLabel} from '../components/StatusBadge';
import type {ResultEvidence} from '../api/types';

export function ResultDocument(){
 const {id}=useParams(),result=useData<ResultEvidence>('/requests/'+id+'/result'),item=result.data,snapshot=item?.snapshot;
 return <div className="result-page"><div className="result-actions"><Link to={'/app/requests/'+id}>Kembali ke permohonan</Link><Button disabled={!item} onClick={()=>window.print()}>Cetak / simpan PDF</Button></div><PageState {...result}/>{item&&snapshot&&<article className="result-sheet"><header><span className="eyebrow">SGWA · HASIL LAYANAN</span><h1>Bukti hasil</h1><p className="result-demo-label">{item.label}</p><p className="subtle">{item.number}</p></header>{snapshot.converted&&<p className="conversion-note">Hasil konversi dari keputusan historis. Informasi yang tidak tercatat ditampilkan sebagai tidak tersedia.</p>}<dl className="result-metadata"><div><dt>Referensi permohonan</dt><dd>{snapshot.reference}</dd></div><div><dt>Pemohon</dt><dd>{snapshot.owner_name}</dd></div><div><dt>Permohonan</dt><dd>{snapshot.title}</dd></div><div><dt>Keputusan akhir</dt><dd>{statusLabel[snapshot.status]}</dd></div><div><dt>Waktu finalisasi</dt><dd>{snapshot.finalized_at?date(snapshot.finalized_at)+' WIB':'Tidak tercatat'}</dd></div></dl><section><h2>Ringkasan keputusan</h2><p className="request-description">{snapshot.notes??'Tidak tercatat'}</p></section><section><h2>Keputusan instansi</h2>{snapshot.agency_decisions.length?snapshot.agency_decisions.map(task=><div className="result-decision" key={task.agency_id}><h3>{task.agency_name}</h3><p>{statusLabel[task.status]} · {task.completed_at?date(task.completed_at)+' WIB':'Waktu selesai tidak tercatat'}</p><p className="request-description">{task.note??'Catatan tidak tercatat'}</p></div>):<p>Keputusan instansi tidak tercatat.</p>}</section><footer>Snapshot keputusan tersimpan. Nomor ini digunakan untuk demo akademik dan tidak memiliki verifikasi publik atau tanda tangan elektronik resmi.</footer></article>}</div>;
}
