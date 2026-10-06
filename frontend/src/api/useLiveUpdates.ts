import {useEffect,useState} from 'react';
import type {User} from './types';
import {api} from './client';
export type LiveStatus='idle'|'connecting'|'connected'|'reconnecting';
export function useLiveUpdates(user:User|null):LiveStatus{
 const [status,setStatus]=useState<LiveStatus>('idle');
 useEffect(()=>{
  if(!user){setStatus('idle');return}
  let active=true,checking=false,authorized=false,pending=false;setStatus('connecting');
  const stream=new EventSource('/api/v1/live',{withCredentials:true});
  const refresh=()=>{if(active&&authorized){setStatus('connected');window.dispatchEvent(new Event('sgwa:data-changed'))}};
  const changed=()=>{if(!authorized)pending=true;else refresh()};
  const invalid=()=>{stream.close();if(active)window.dispatchEvent(new Event('sgwa:unauthorized'))};
  const unavailable=()=>{authorized=false;if(active)setStatus('reconnecting')};
  const check=()=>{if(checking||!active)return;checking=true;api<User>('/auth/me').then(current=>{if(!active)return;if(current.id!==user.id||current.role!==user.role||current.agency_id!==user.agency_id||!current.active){invalid();return}authorized=true;setStatus('connected');if(pending){pending=false;refresh()}}).catch(()=>{}).finally(()=>{checking=false})};
  const connected=()=>{authorized=false;check()};
  const error=()=>{unavailable();check()};
  stream.addEventListener('changed',changed);stream.addEventListener('open',connected);stream.addEventListener('session-invalid',invalid);stream.addEventListener('unavailable',unavailable);stream.addEventListener('error',error);
  return()=>{active=false;stream.close()};
 },[user?.id,user?.role,user?.agency_id]);
 return status;
}
