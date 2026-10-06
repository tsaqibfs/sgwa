import {useEffect,useState} from 'react';
import type {User} from './types';
import {api} from './client';
export type LiveStatus='idle'|'connecting'|'connected'|'reconnecting';
export function useLiveUpdates(user:User|null):LiveStatus{
 const [status,setStatus]=useState<LiveStatus>('idle');
 useEffect(()=>{
  if(!user){setStatus('idle');return}
  let active=true,checking=false;setStatus('connecting');
  const stream=new EventSource('/api/v1/live',{withCredentials:true});
  const changed=()=>{if(active){setStatus('connected');window.dispatchEvent(new Event('sgwa:data-changed'))}};
  const connected=()=>{if(active)setStatus('connected')};
  const invalid=()=>{stream.close();if(active)window.dispatchEvent(new Event('sgwa:unauthorized'))};
  const unavailable=()=>{if(active)setStatus('reconnecting')};
  const error=()=>{unavailable();if(checking||!active)return;checking=true;api<User>('/auth/me').catch(()=>{}).finally(()=>{checking=false})};
  stream.addEventListener('changed',changed);stream.addEventListener('open',connected);stream.addEventListener('session-invalid',invalid);stream.addEventListener('unavailable',unavailable);stream.addEventListener('error',error);
  return()=>{active=false;stream.close()};
 },[user?.id,user?.role,user?.agency_id]);
 return status;
}
