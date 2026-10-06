import {useEffect,useState,useCallback,useRef} from 'react';
import {api} from './client';
export function useData<T>(path:string){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[revision,setRevision]=useState(0);
 const reload=useCallback(()=>setRevision(n=>n+1),[]);
 const latest=useRef<T|null>(null),lastPath=useRef(path);
 useEffect(()=>{window.addEventListener('sgwa:data-changed',reload);return()=>window.removeEventListener('sgwa:data-changed',reload)},[reload]);
 useEffect(()=>{
  let active=true;
  if(lastPath.current!==path){latest.current=null;setData(null);lastPath.current=path}
  setLoading(latest.current===null);setError('');
  api<T>(path).then(value=>{if(active){latest.current=value;setData(value)}}).catch(exc=>{if(active)setError(exc.message)}).finally(()=>{if(active)setLoading(false)});
  return()=>{active=false};
 },[path,revision]);
 return {data,error,loading,reload};
}
