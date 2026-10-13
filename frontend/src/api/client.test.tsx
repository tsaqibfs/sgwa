import {afterEach,it,expect,vi} from 'vitest';
import * as client from './client';
afterEach(()=>vi.unstubAllGlobals());
function file(){expect(client).toHaveProperty('apiFile');return (client as typeof client&{apiFile:(path:string)=>Promise<{blob:Blob;filename:string;generatedAt:string|null}>}).apiFile}
function readBlob(blob:Blob):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=()=>reject(reader.error);reader.readAsText(blob)})}

it('downloads CSV using cookies and trusted server filename',async()=>{
 const fetch=vi.fn().mockResolvedValue(new Response('\ufeffheader\r\nrow\r\n',{headers:{'content-type':'text/csv; charset=utf-8','content-disposition':'attachment; filename="sgwa-laporan-20261013-010000.csv"','x-report-generated-at':'2026-10-13T01:00:00Z'}}));vi.stubGlobal('fetch',fetch);
 const result=await file()('/reports/requests.csv');expect(await readBlob(result.blob)).toContain('header');expect(result.filename).toBe('sgwa-laporan-20261013-010000.csv');expect(result.generatedAt).toBe('2026-10-13T01:00:00Z');expect(fetch.mock.calls[0][1].credentials).toBe('include');
});
it.each([413,503])('rejects JSON error %i instead of saving it as a CSV',async status=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Persempit filter'}),{status,headers:{'content-type':'application/json'}})));
 await expect(file()('/reports/requests.csv')).rejects.toMatchObject({status,message:'Persempit filter'});
});
it('dispatches session expiry for a CSV 401',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Sesi berakhir'}),{status:401})));const listener=vi.fn();window.addEventListener('sgwa:unauthorized',listener);
 try{await expect(file()('/reports/requests.csv')).rejects.toMatchObject({status:401});expect(listener).toHaveBeenCalledOnce()}finally{window.removeEventListener('sgwa:unauthorized',listener)}
});
it('rejects successful JSON from proxy rather than producing fake file',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{}',{headers:{'content-type':'application/json'}})));await expect(file()('/reports/requests.csv')).rejects.toMatchObject({status:502});
});
it('rejects network failure with existing ApiError contract',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('offline')));await expect(file()('/reports/requests.csv')).rejects.toMatchObject({status:0});
});
it('falls back from unsafe filename and accepts header-only CSV',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('header\r\n',{headers:{'content-type':'text/csv','content-disposition':'attachment; filename="../../secret.csv"'}})));const result=await file()('/reports/requests.csv');expect(result.filename).toBe('sgwa-laporan.csv');expect(await readBlob(result.blob)).toBe('header\r\n');
});
it('preserves JSON API validation and successful body handling',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(new Response('{"total":1}')).mockResolvedValueOnce(new Response('{"detail":[{"msg":"bad"}]}',{status:422})));
 expect(await client.api('/reports')).toEqual({total:1});await expect(client.api('/reports')).rejects.toMatchObject({status:422,message:'Periksa kembali isian formulir Anda.'});
});
