import {useEffect,useRef,useState,type FormEvent,type ReactNode} from 'react';
import {Button,TextArea,TextField} from '@radix-ui/themes';
import {ArrowRight} from '@phosphor-icons/react';
import type {Draft} from '../api/types';

type FieldErrors = Partial<Record<keyof Draft,string>>;

export function RequestForm({onSubmit,draft,onChange,children}:{onSubmit:(value:Draft)=>Promise<unknown>;draft?:Draft;onChange?:(value:Draft)=>void;children?:ReactNode}){
 const [local,setLocal]=useState<Draft>({title:'',description:''});
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [fieldErrors,setFieldErrors]=useState<FieldErrors>({});
 const invalid=Object.entries(fieldErrors);
 const summaryRef=useRef<HTMLDivElement>(null);
 const value=draft??local;

 useEffect(()=>{
  if(error||Object.keys(fieldErrors).length)summaryRef.current?.focus();
 },[error,fieldErrors]);

 function change(next:Draft){setLocal(next);onChange?.(next)}
 async function submit(event:FormEvent){
  event.preventDefault();
  if(busy)return;
  const clean={title:value.title.trim(),description:value.description.trim()};
  const validation:FieldErrors={};
  if(clean.title.length<5||clean.title.length>150)validation.title='Masukkan judul dengan 5–150 karakter.';
  if(clean.description.length<20||clean.description.length>5000)validation.description='Jelaskan kebutuhan dalam 20–5.000 karakter.';
  setError('');
  setFieldErrors(validation);
  if(Object.keys(validation).length)return;
  setBusy(true);
  try{await onSubmit(clean)}
  catch(exc){setError(exc instanceof Error?exc.message:'Pengajuan gagal. Silakan coba kembali.')}
  finally{setBusy(false)}
 }

 return <form onSubmit={submit} noValidate className="request-form">
  {(invalid.length>0||error)&&<div ref={summaryRef} className="error form-error-summary" role="alert" tabIndex={-1}>
   <h2>{error?'Permohonan belum terkirim':'Periksa isian permohonan'}</h2>
   {error ? <p>{error}</p> : <ul>{invalid.map(([key,message])=><li key={key}><a href={'#request-'+key} onClick={event=>{event.preventDefault();document.getElementById('request-'+key)?.focus()}}>{message}</a></li>)}</ul>}
  </div>}
  <label htmlFor="request-title">Judul permohonan</label>
  {fieldErrors.title&&<p className="field-error" id="request-title-error">{fieldErrors.title}</p>}
  <TextField.Root id="request-title" size="3" value={value.title} onChange={e=>change({...value,title:e.target.value})} maxLength={150} placeholder="Contoh: Pengurusan KTP yang hilang" aria-invalid={!!fieldErrors.title} aria-describedby={fieldErrors.title?'request-title-error':undefined}/>
  <label htmlFor="request-description">Ceritakan kebutuhan Anda</label>
  {fieldErrors.description&&<p className="field-error" id="request-description-error">{fieldErrors.description}</p>}
  <TextArea id="request-description" size="3" rows={7} value={value.description} onChange={e=>change({...value,description:e.target.value})} maxLength={5000} placeholder="Tuliskan kebutuhan dan kendala Anda secara jelas." aria-invalid={!!fieldErrors.description} aria-describedby={fieldErrors.description?'request-description-error request-privacy-hint':'request-privacy-hint'}/>
  <div className="form-hint"><span id="request-privacy-hint">Hindari mencantumkan NIK atau informasi pribadi sensitif.</span><span>{value.description.length.toLocaleString('id-ID')} / 5.000</span></div>
  {children}
  <Button type="submit" size="3" loading={busy}>Kirim permohonan <ArrowRight/></Button>
 </form>;
}
