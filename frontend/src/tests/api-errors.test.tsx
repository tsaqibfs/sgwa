import { describe,it,expect,vi,afterEach } from 'vitest';
import { api,ApiError } from '../api/client';
afterEach(()=>vi.unstubAllGlobals());
describe('Kesalahan API',()=>{
 it('mempertahankan kode konflik tanpa mencoba ulang mutasi',async()=>{
  const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Muat ulang permohonan'}),{status:409}));vi.stubGlobal('fetch',fetch);
  await expect(api('/requests/1/status',{method:'PATCH',body:'{}'})).rejects.toMatchObject({status:409,message:'Muat ulang permohonan'});
  expect(fetch).toHaveBeenCalledTimes(1);
 });
 it('memberi peristiwa sesi berakhir pada respons 401',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Sesi berakhir'}),{status:401})));
  const listener=vi.fn();window.addEventListener('sgwa:unauthorized',listener);
  await expect(api('/auth/me')).rejects.toBeInstanceOf(ApiError);
  expect(listener).toHaveBeenCalledTimes(1);window.removeEventListener('sgwa:unauthorized',listener);
 });
});
