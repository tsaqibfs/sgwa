import {act,renderHook,waitFor} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {useData} from './useData';
afterEach(()=>vi.unstubAllGlobals());

it('exposes background fetching without changing existing loading or stale response guard',async()=>{
 let finish!:(value:Response)=>void;
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(new Response('{"value":1}')).mockImplementationOnce(()=>new Promise<Response>(r=>{finish=r})));
 const {result}=renderHook(()=>useData<{value:number}>('/reports'));
 await waitFor(()=>expect(result.current.data?.value).toBe(1));expect(result.current.fetching).toBe(false);
 act(()=>result.current.reload());await waitFor(()=>expect(result.current.fetching).toBe(true));expect(result.current.loading).toBe(false);expect(result.current.data?.value).toBe(1);
 await act(async()=>finish(new Response('{"value":2}')));await waitFor(()=>expect(result.current.fetching).toBe(false));expect(result.current.data?.value).toBe(2);
});
it('ignores late previous filter result and keeps fetching tied to current path',async()=>{
 let first!:(value:Response)=>void,second!:(value:Response)=>void;
 vi.stubGlobal('fetch',vi.fn().mockImplementationOnce(()=>new Promise<Response>(r=>{first=r})).mockImplementationOnce(()=>new Promise<Response>(r=>{second=r})));
 const {result,rerender}=renderHook(({path}:{path:string})=>useData<{value:string}>(path),{initialProps:{path:'/reports?status=pending'}});
 rerender({path:'/reports?status=approved'});await act(async()=>second(new Response('{"value":"approved"}')));await waitFor(()=>expect(result.current.data?.value).toBe('approved'));
 await act(async()=>first(new Response('{"value":"pending"}')));expect(result.current.data?.value).toBe('approved');expect(result.current.fetching).toBe(false);
});
