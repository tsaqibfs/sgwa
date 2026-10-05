import {useEffect,useState,useCallback} from 'react';
import {api} from './client';
export function useData<T>(path:string){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[revision,setRevision]=useState(0);
 const reload=useCallback(()=>setRevision(n=>n+1),[]);
 useEffect(()=>{let active=true;setLoading(true);setError('');api<T>(path).then(value=>{if(active)setData(value)}).catch(exc=>{if(active)setError(exc.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[path,revision]);
 return {data,error,loading,reload};
}
