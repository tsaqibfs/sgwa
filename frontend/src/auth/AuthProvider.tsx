import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {api,bootstrapCsrf} from '../api/client';
import type {User,Draft} from '../api/types';
import {useLiveUpdates,type LiveStatus} from '../api/useLiveUpdates';
type DecisionDraft={note:string;target:string;additionalTargets?:number[]};
type Auth={user:User|null;loading:boolean;liveStatus:LiveStatus;setUser:(user:User|null)=>void;refreshUser:()=>Promise<void>;logout:()=>Promise<void>;draft:Draft;setDraft:(draft:Draft)=>void;decisionDraft:(id:string)=>DecisionDraft;setDecisionDraft:(id:string,draft:DecisionDraft)=>void};
const Context=createContext<Auth|null>(null);
export function AuthProvider({children}:{children:ReactNode}){
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true);
 const liveStatus=useLiveUpdates(user);
 const [drafts,setDrafts]=useState<Record<string,Draft>>({});
 const [decisions,setDecisions]=useState<Record<string,DecisionDraft>>({});
 const userKey=String(user?.id??'anonymous');
 const draft=drafts[userKey]??{title:'',description:''};
 function setDraft(value:Draft){setDrafts(current=>({...current,[userKey]:value}))}
 function decisionDraft(id:string){return decisions[userKey+':'+id]??{note:'',target:''}}
 function setDecisionDraft(id:string,value:DecisionDraft){setDecisions(current=>({...current,[userKey+':'+id]:value}))}
 useEffect(()=>{
  const expired=()=>setUser(null);window.addEventListener('sgwa:unauthorized',expired);
  bootstrapCsrf().then(()=>api<User>('/auth/me')).then(setUser).catch(()=>{}).finally(()=>setLoading(false));
  return()=>window.removeEventListener('sgwa:unauthorized',expired);
 },[]);
 async function logout(){await bootstrapCsrf();await api('/auth/logout',{method:'POST'});setUser(null);setDrafts({});setDecisions({});await bootstrapCsrf()}
 async function refreshUser(){setUser(await api<User>('/auth/me'))}
 return <Context.Provider value={{user,loading,liveStatus,setUser,refreshUser,logout,draft,setDraft,decisionDraft,setDecisionDraft}}>{children}</Context.Provider>;
}
export function useAuth(){const value=useContext(Context);if(!value)throw new Error('AuthProvider required');return value}
