import {renderHook,act,waitFor} from '@testing-library/react';
import {it,expect,vi,afterEach} from 'vitest';
import {useLiveUpdates} from '../api/useLiveUpdates';
import {useData} from '../api/useData';
import type {User} from '../api/types';
const user:User={id:1,name:'Warga',email:'warga@test.id',role:'citizen',agency_id:null,active:true};
class Stream extends EventTarget{static instances:Stream[]=[];close=vi.fn();constructor(){super();Stream.instances.push(this)}}
afterEach(()=>{vi.unstubAllGlobals();Stream.instances=[]});
it('menghapus data ketika akses detail hilang tanpa mempertahankan data stale',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({version:1}))).mockResolvedValueOnce(new Response(JSON.stringify({detail:'Tidak ditemukan'}),{status:404}));vi.stubGlobal('fetch',fetch);
 const {result}=renderHook(()=>useData<{version:number}>('/requests/1'));
 await waitFor(()=>expect(result.current.data?.version).toBe(1));
 act(()=>window.dispatchEvent(new Event('sgwa:data-changed')));
 await waitFor(()=>expect(result.current.error).toBe('Tidak ditemukan'));
 expect(result.current.data).toBeNull();
});
it('memvalidasi ulang scope pada reconnect sebelum menyegarkan data',async()=>{
 vi.stubGlobal('EventSource',Stream);vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({...user,role:'staff',agency_id:2}))));
 const invalid=vi.fn(),changed=vi.fn();window.addEventListener('sgwa:unauthorized',invalid);window.addEventListener('sgwa:data-changed',changed);
 const {unmount}=renderHook(()=>useLiveUpdates({...user,role:'staff',agency_id:1}));
 act(()=>{Stream.instances[0].dispatchEvent(new Event('open'));Stream.instances[0].dispatchEvent(new Event('changed'))});
 await waitFor(()=>expect(invalid).toHaveBeenCalledOnce());expect(changed).not.toHaveBeenCalled();expect(Stream.instances[0].close).toHaveBeenCalledOnce();
 unmount();window.removeEventListener('sgwa:unauthorized',invalid);window.removeEventListener('sgwa:data-changed',changed);
});
it('memperbarui data pada sinyal dan menutup stream ketika logout',async()=>{
 vi.stubGlobal('EventSource',Stream);vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify(user))));const changed=vi.fn();window.addEventListener('sgwa:data-changed',changed);
 const {rerender,unmount}=renderHook(({actor}:{actor:User|null})=>useLiveUpdates(actor),{initialProps:{actor:user as User|null}});
 act(()=>{Stream.instances[0].dispatchEvent(new Event('open'));Stream.instances[0].dispatchEvent(new Event('changed'))});await waitFor(()=>expect(changed).toHaveBeenCalledOnce());
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
