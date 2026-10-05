import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {api,bootstrapCsrf} from '../api/client';
import type {User,Draft} from '../api/types';
type Auth={user:User|null;loading:boolean;setUser:(user:User|null)=>void;logout:()=>Promise<void>;draft:Draft;setDraft:(draft:Draft)=>void};
const Context=createContext<Auth|null>(null);
export function AuthProvider({children}:{children:ReactNode}){
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true);
 const [draft,setDraft]=useState<Draft>({title:'',description:''});
 useEffect(()=>{
  const expired=()=>setUser(null);window.addEventListener('sgwa:unauthorized',expired);
  bootstrapCsrf().then(()=>api<User>('/auth/me')).then(setUser).catch(()=>{}).finally(()=>setLoading(false));
  return()=>window.removeEventListener('sgwa:unauthorized',expired);
 },[]);
 async function logout(){await bootstrapCsrf();await api('/auth/logout',{method:'POST'});setUser(null);setDraft({title:'',description:''});await bootstrapCsrf()}
 return <Context.Provider value={{user,loading,setUser,logout,draft,setDraft}}>{children}</Context.Provider>;
}
export function useAuth(){const value=useContext(Context);if(!value)throw new Error('AuthProvider required');return value}
