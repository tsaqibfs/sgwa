import {useState,type FormEvent,type ReactNode} from 'react';
import {Button,TextArea,TextField} from '@radix-ui/themes';
import {ArrowRight,Info} from '@phosphor-icons/react';
import type {Draft} from '../api/types';
export function RequestForm({onSubmit,draft,onChange,children}:{onSubmit:(value:Draft)=>Promise<unknown>;draft?:Draft;onChange?:(value:Draft)=>void;children?:ReactNode}){
 const [local,setLocal]=useState<Draft>({title:'',description:''}),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const value=draft??local;
 function change(next:Draft){setLocal(next);onChange?.(next)}
 async function submit(event:FormEvent){
  event.preventDefault();if(busy)return;
  const clean={title:value.title.trim(),description:value.description.trim()};
  if(clean.title.length<5||clean.title.length>150||clean.description.length<20||clean.description.length>5000){setError('Judul perlu 5–150 karakter dan cerita kebutuhan 20–5.000 karakter.');return}
  setBusy(true);setError('');
  try{await onSubmit(clean)}catch(exc){setError(exc instanceof Error?exc.message:'Pengajuan gagal. Silakan coba kembali.')}finally{setBusy(false)}
 }
 return <form onSubmit={submit} noValidate className="request-form">
  <label htmlFor="request-title">Judul permohonan</label><TextField.Root id="request-title" size="3" value={value.title} onChange={e=>change({...value,title:e.target.value})} maxLength={150} placeholder="Contoh: Pengurusan KTP yang hilang"/>
  <label htmlFor="request-description">Ceritakan kebutuhan Anda</label><TextArea id="request-description" size="3" rows={7} value={value.description} onChange={e=>change({...value,description:e.target.value})} maxLength={5000} placeholder="Tuliskan kebutuhan dan kendala Anda secara jelas. Sistem akan membantu menemukan dinas yang tepat."/>
  <div className="form-hint"><span>Hindari mencantumkan NIK atau informasi pribadi sensitif.</span><span>{value.description.length.toLocaleString('id-ID')} / 5.000</span></div>
  {children}
  <div className="info-strip"><Info size={21}/><p>ML membantu menentukan dinas tujuan. Keputusan layanan tetap dibuat oleh petugas.</p></div>
  {error&&<p role="alert" className="error">{error}</p>}
  <Button type="submit" size="3" loading={busy}>Kirim permohonan <ArrowRight/></Button>
 </form>;
}
