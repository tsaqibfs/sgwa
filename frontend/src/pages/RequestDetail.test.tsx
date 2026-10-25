import {act,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import {Theme} from '@radix-ui/themes';
import userEvent from '@testing-library/user-event';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {RequestDetail} from './RequestDetail';
import type {RequestItem,User} from '../api/types';

const auth=vi.hoisted(()=>({user:{id:1,name:'Warga',email:'warga@test.id',role:'citizen',agency_id:null,active:true} as User}));
vi.mock('../auth/AuthProvider',async()=>{
 const {useState}=await import('react');
 return {useAuth:()=>{
  const [draft,setDraft]=useState({note:'',target:'',additionalTargets:[] as number[]});
  return {user:auth.user,decisionDraft:()=>draft,setDecisionDraft:(_id:string,value:typeof draft)=>setDraft(value)};
 }};
});
let item:RequestItem;
beforeEach(()=>{
 auth.user.role='citizen';
 item={id:1,reference:'SGWA-TEST',citizen_id:1,title:'Permohonan untuk diperiksa',description:'Kebutuhan layanan yang diperiksa oleh admin.',assigned_agency_id:null,agency_name:null,status:'escalated',version:1,created_at:'2026-10-23T01:00:00Z',updated_at:'2026-10-23T01:00:00Z',workflows:[],classification:null,events:[],attachments:[]};
 vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/requests/1')?item:url.endsWith('/agencies')?[{id:7,name:'DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL',code:'dukcapil',active:true,sla_days:3,description:''}]:url.includes('/ml/feedback?')?{items:[],total:0,page:1,page_size:100}:[]),{headers:{'content-type':'application/json'}})));
});
afterEach(()=>vi.unstubAllGlobals());
function show(){render(<Theme><MemoryRouter initialEntries={['/app/requests/1']}><Routes><Route path="/app/requests/:id" element={<RequestDetail/>}/></Routes></MemoryRouter></Theme>)}
function primary(){return screen.getByText('Dinas utama').querySelector('strong')!}

it.each(['approved','rejected'] as const)('menjelaskan keputusan langsung admin pada permohonan %s tanpa dinas',async status=>{
 item.status=status;show();
 await screen.findByRole('heading',{name:item.title});
 expect(primary()).toHaveTextContent('Ditangani langsung oleh admin');
 expect(screen.queryByText('Menunggu pemeriksaan admin')).not.toBeInTheDocument();
 expect(screen.queryByText('Dinas tujuan ditetapkan setelah pemeriksaan admin.')).not.toBeInTheDocument();
 expect(screen.getByText('Tidak ada penugasan dinas yang tercatat untuk permohonan ini.')).toBeVisible();
});
it('tetap menjelaskan pemeriksaan yang belum selesai',async()=>{
 show();await screen.findByRole('heading',{name:item.title});
 expect(primary()).toHaveTextContent('Menunggu pemeriksaan admin');
});
it('memperbarui keterangan setelah keputusan admin dan mempertahankan nama dinas yang ditetapkan',async()=>{
 show();await screen.findByRole('heading',{name:item.title});
 expect(primary()).toHaveTextContent('Menunggu pemeriksaan admin');
 item={...item,status:'approved',version:2};
 act(()=>window.dispatchEvent(new Event('sgwa:data-changed')));
 await waitFor(()=>expect(primary()).toHaveTextContent('Ditangani langsung oleh admin'));
 item={...item,assigned_agency_id:7,agency_name:'DINAS KESEHATAN',version:3};
 act(()=>window.dispatchEvent(new Event('sgwa:data-changed')));
 await waitFor(()=>expect(primary()).toHaveTextContent('DINAS KESEHATAN'));
 expect(primary()).not.toHaveTextContent('Ditangani langsung oleh admin');
});
it('membedakan persetujuan langsung dan penyaluran ke dinas pada petunjuk admin',async()=>{
 auth.user.role='admin';show();await screen.findByRole('heading',{name:item.title});
 expect(screen.getByText('Untuk meminta dinas menindaklanjuti, pilih dinas lalu klik “Alihkan permohonan”. Tombol “Disetujui” menyelesaikan permohonan langsung oleh admin dan tidak menetapkan dinas.')).toBeVisible();
});
it('mengarahkan pilihan dinas ke endpoint penugasan dan mencegah persetujuan langsung mengabaikannya',async()=>{
 auth.user.role='admin';const user=userEvent.setup();show();
 await screen.findByRole('heading',{name:item.title});
 await user.type(screen.getByLabelText('Catatan keputusan'),'Teruskan untuk penggantian KTP.');
 await user.selectOptions(screen.getByLabelText('Alihkan ke dinas'),'7');
 expect(screen.getByRole('button',{name:'Disetujui'})).toBeDisabled();
 expect(screen.getByRole('button',{name:'Ditolak'})).toBeDisabled();
 expect(screen.getByText('Dinas tujuan sudah dipilih. Klik “Alihkan permohonan” di bawah untuk mengirim tugas ke dinas tersebut. Kosongkan pilihan dinas jika ingin menetapkan keputusan akhir langsung.')).toBeVisible();
 const route=screen.getByRole('button',{name:'Alihkan permohonan'});expect(route).toBeEnabled();await user.click(route);
 await waitFor(()=>expect(vi.mocked(fetch).mock.calls.some(([url,options])=>String(url).endsWith('/review-route')&&options?.method==='POST')).toBe(true));
 const call=vi.mocked(fetch).mock.calls.find(([url])=>String(url).endsWith('/review-route'))!;
 expect(JSON.parse(String(call[1]?.body))).toEqual({version:1,agency_ids:[7],note:'Teruskan untuk penggantian KTP.'});
 expect(vi.mocked(fetch).mock.calls.some(([url])=>String(url).endsWith('/status'))).toBe(false);
});
it('tetap memungkinkan keputusan langsung setelah pilihan penugasan dikosongkan',async()=>{
 auth.user.role='admin';const user=userEvent.setup();show();
 await screen.findByRole('heading',{name:item.title});
 await user.type(screen.getByLabelText('Catatan keputusan'),'Admin menyelesaikan langsung.');
 await user.selectOptions(screen.getByLabelText('Alihkan ke dinas'),'7');
 await user.selectOptions(screen.getByLabelText('Alihkan ke dinas'),'');
 expect(screen.getByRole('button',{name:'Disetujui'})).toBeEnabled();
 await user.click(screen.getByRole('button',{name:'Disetujui'}));
 await user.click(screen.getByRole('button',{name:'Konfirmasi'}));
 await waitFor(()=>expect(vi.mocked(fetch).mock.calls.some(([url])=>String(url).endsWith('/status'))).toBe(true));
 expect(vi.mocked(fetch).mock.calls.some(([url])=>String(url).endsWith('/review-route'))).toBe(false);
});
it.each(['citizen','staff'] as const)('menyembunyikan panel ML dan menggunakan satu kolom untuk %s meski respons lama berisi prediksi',async role=>{
 auth.user.role=role;
 item.classification={predicted_agency_code:'dukcapil',probabilities:{dukcapil:.9},confidence:.9,needs_review:true,model_version:'visibility-fixture'};
 show();await screen.findByRole('heading',{name:item.title});
 expect(screen.queryByText('KLASIFIKASI ML')).not.toBeInTheDocument();
 expect(document.querySelector('.classification-panel')).toBeNull();
 expect(document.querySelector('.detail-layout')).toHaveClass('detail-layout--single');
 expect(screen.queryByText('visibility-fixture',{exact:false})).not.toBeInTheDocument();
});
it('tetap menampilkan panel dan rincian prediksi kepada admin',async()=>{
 auth.user.role='admin';
 item.classification={predicted_agency_code:'dukcapil',probabilities:{dukcapil:.9},confidence:.9,needs_review:true,model_version:'visibility-fixture'};
 show();await screen.findByRole('heading',{name:item.title});
 expect(screen.getByText('KLASIFIKASI ML')).toBeVisible();
 expect(screen.getByRole('heading',{name:'dukcapil'})).toBeVisible();
 expect(screen.getByText('Model: visibility-fixture')).toBeVisible();
 expect(document.querySelector('.detail-layout')).not.toHaveClass('detail-layout--single');
});

it('menyimpan pilihan dinas pendamping saat daftar ditutup dan mengirimkannya bersama dinas utama',async()=>{
 auth.user.role='admin';const user=userEvent.setup();
 const original=vi.mocked(fetch).getMockImplementation()!;
 vi.mocked(fetch).mockImplementation(async(url,options)=>String(url).endsWith('/agencies')?new Response(JSON.stringify([{id:7,name:'Dukcapil',active:true},{id:8,name:'Dinas Kesehatan',active:true}]),{headers:{'content-type':'application/json'}}):original(url,options));
 show();await screen.findByRole('heading',{name:item.title});
 await user.type(screen.getByLabelText('Catatan keputusan'),'Koordinasi dengan dinas pendamping.');
 await user.selectOptions(screen.getByLabelText('Alihkan ke dinas'),'7');
 expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
 await user.click(screen.getByRole('button',{name:'Tambah dinas pendamping'}));
 await user.click(screen.getByRole('checkbox',{name:'Dinas Kesehatan'}));
 await user.click(screen.getByRole('button',{name:'Tutup pilihan dinas'}));
 expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
 expect(screen.getByText('Dinas pendamping dipilih: Dinas Kesehatan')).toBeVisible();
 await user.click(screen.getByRole('button',{name:'Tambah dinas pendamping'}));
 expect(screen.getByRole('checkbox',{name:'Dinas Kesehatan'})).toBeChecked();
 await user.click(screen.getByRole('button',{name:'Alihkan permohonan'}));
 await waitFor(()=>expect(vi.mocked(fetch).mock.calls.some(([url])=>String(url).endsWith('/review-route'))).toBe(true));
 const call=vi.mocked(fetch).mock.calls.find(([url])=>String(url).endsWith('/review-route'))!;
 expect(JSON.parse(String(call[1]?.body)).agency_ids).toEqual([7,8]);
});
