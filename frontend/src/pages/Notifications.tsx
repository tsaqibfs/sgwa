import {useState} from 'react';
import {Link} from 'react-router-dom';
import {Button} from '@radix-ui/themes';
import {api} from '../api/client';
import {useData} from '../api/useData';
import {PageState} from '../components/PageState';
import {date} from '../components/RequestTimeline';
import type {NoticeList} from '../api/types';

export function Notifications(){
 const [page,setPage]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const result=useData<NoticeList>('/notifications?page='+page);
 async function read(id?:number){setBusy(true);setError('');try{await api(id?'/notifications/'+id+'/read':'/notifications/read-all',{method:id?'PATCH':'POST'});window.dispatchEvent(new Event('sgwa:data-changed'))}catch(exc){setError((exc as Error).message)}finally{setBusy(false)}}
 return <><div className="page-heading"><div><span className="eyebrow">INBOX LAYANAN</span><h1>Notifikasi</h1><p>Pembaruan tersimpan agar riwayat layanan tetap mudah diikuti.</p></div><Button variant="soft" disabled={busy||!result.data?.total} onClick={()=>read()}>Tandai semua dibaca</Button></div>{error&&<p role="alert" className="error">{error}</p>}<section className="panel"><PageState {...result}/>{result.data?.items.map(notice=><article key={notice.id} className={'notification-row '+(!notice.read_at?'unread':'')}><div><strong>{notice.title}</strong><p className="subtle">{date(notice.created_at)} WIB · {notice.read_at?'Sudah dibaca':'Belum dibaca'}</p>{notice.read_at&&<small>Sudah dibaca</small>}{notice.can_open_request&&<Link to={'/app/requests/'+notice.request_id}>Buka permohonan</Link>}</div>{!notice.read_at&&<Button variant="outline" disabled={busy} onClick={()=>read(notice.id)}>Tandai dibaca</Button>}</article>)}{result.data?.total===0&&<p>Belum ada notifikasi.</p>}{result.data&&result.data.total>0&&<div className="pagination"><span>{result.data.total} notifikasi · halaman {page}</span><Button variant="outline" disabled={page===1} onClick={()=>setPage(n=>n-1)}>Sebelumnya</Button><Button variant="outline" disabled={page*20>=result.data.total} onClick={()=>setPage(n=>n+1)}>Berikutnya</Button></div>}</section></>;
}
