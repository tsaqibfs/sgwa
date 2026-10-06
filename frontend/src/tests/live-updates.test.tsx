import {renderHook,act,waitFor} from '@testing-library/react';
import {it,expect,vi,afterEach} from 'vitest';
import {useLiveUpdates} from '../api/useLiveUpdates';
import {useData} from '../api/useData';
import type {User} from '../api/types';
const user:User={id:1,name:'Warga',email:'warga@test.id',role:'citizen',agency_id:null,active:true};
class Stream extends EventTarget{static instances:Stream[]=[];close=vi.fn();constructor(){super();Stream.instances.push(this)}}
afterEach(()=>{vi.unstubAllGlobals();Stream.instances=[]});
it('memperbarui data pada sinyal dan menutup stream ketika logout',()=>{
 vi.stubGlobal('EventSource',Stream);const changed=vi.fn();window.addEventListener('sgwa:data-changed',changed);
 const {rerender,unmount}=renderHook(({actor}:{actor:User|null})=>useLiveUpdates(actor),{initialProps:{actor:user as User|null}});
 act(()=>Stream.instances[0].dispatchEvent(new Event('changed')));expect(changed).toHaveBeenCalledOnce();
 rerender({actor:null});expect(Stream.instances[0].close).toHaveBeenCalledOnce();unmount();window.removeEventListener('sgwa:data-changed',changed);
});
it('menjaga data lama selama refresh dan mengabaikan respons lama',async()=>{
 let first!:(value:Response)=>void,latest!:(value:Response)=>void;
 const fetch=vi.fn().mockImplementationOnce(()=>new Promise<Response>(r=>{first=r})).mockImplementationOnce(()=>new Promise<Response>(r=>{latest=r}));vi.stubGlobal('fetch',fetch);
 const {result}=renderHook(()=>useData<{version:number}>('/requests/1'));
 act(()=>window.dispatchEvent(new Event('sgwa:data-changed')));await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2));
 await act(async()=>latest(new Response(JSON.stringify({version:2}))));await waitFor(()=>expect(result.current.data?.version).toBe(2));
 await act(async()=>first(new Response(JSON.stringify({version:1}))));expect(result.current.data?.version).toBe(2);
 let refresh!:(value:Response)=>void;fetch.mockImplementationOnce(()=>new Promise<Response>(r=>{refresh=r}));
 act(()=>window.dispatchEvent(new Event('sgwa:data-changed')));await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(3));
 expect(result.current.loading).toBe(false);expect(result.current.data?.version).toBe(2);
 await act(async()=>refresh(new Response(JSON.stringify({version:3}))));await waitFor(()=>expect(result.current.data?.version).toBe(3));
});
