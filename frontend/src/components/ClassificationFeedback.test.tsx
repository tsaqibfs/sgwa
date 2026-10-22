import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {Theme} from '@radix-ui/themes';
import {vi,describe,it,expect,beforeEach} from 'vitest';
import {ClassificationFeedback} from './ClassificationFeedback';
import {ApiError} from '../api/client';

const {call}=vi.hoisted(()=>({call:vi.fn()}));
vi.mock('../api/client',async original=>({...await original<typeof import('../api/client')>(),api:call}));

describe('classification feedback',()=>{
 beforeEach(()=>{call.mockReset();call.mockImplementation(async(path:string)=>path==='/ml/labels'?[{code:'pendidikan',name:'DINAS PENDIDIKAN',active:true}]:{items:[],total:0,page:1,page_size:100})});
 it('requires explicit provenance and keeps submitted correction after conflict',async()=>{
  const user=userEvent.setup();render(<Theme><ClassificationFeedback requestId={42}/></Theme>);
  await screen.findByRole('option',{name:'DINAS PENDIDIKAN'});
  await user.selectOptions(screen.getByLabelText('Kelas utama yang benar'),'pendidikan');
  await user.type(screen.getByLabelText('Teks training yang sudah disunting'),'Memohon bantuan beasiswa siswa sekolah.');
  await user.type(screen.getByLabelText('Alasan koreksi'),'Layanan sekolah sudah diperiksa.');
  expect(screen.getByRole('button',{name:'Simpan koreksi'})).toBeDisabled();
  await user.selectOptions(screen.getByLabelText('Asal data'),'synthetic_demo');
  call.mockImplementation(async(path:string,options?:RequestInit)=>{
   if(options?.method==='POST')throw new ApiError(409,'Koreksi telah berubah. Muat ulang.');
   if(path==='/ml/labels')return [{code:'pendidikan',name:'DINAS PENDIDIKAN',active:true}];
   return {items:[],total:0,page:1,page_size:100};
  });
  await user.click(screen.getByRole('button',{name:'Simpan koreksi'}));
  await screen.findByRole('alert');
  expect(screen.getByLabelText('Teks training yang sudah disunting')).toHaveValue('Memohon bantuan beasiswa siswa sekolah.');
  expect(screen.getByRole('button',{name:'Simpan koreksi'})).toBeDisabled();
  await user.click(screen.getByRole('button',{name:'Saya sudah meninjau revisi terbaru'}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'Simpan koreksi'})).toBeEnabled());
 });
 it('rejects whitespace-only reason',async()=>{
  const user=userEvent.setup();render(<Theme><ClassificationFeedback requestId={42}/></Theme>);
  await screen.findByRole('option',{name:'DINAS PENDIDIKAN'});
  await user.selectOptions(screen.getByLabelText('Kelas utama yang benar'),'pendidikan');
  await user.selectOptions(screen.getByLabelText('Asal data'),'real');
  await user.type(screen.getByLabelText('Teks training yang sudah disunting'),'Teks tentang bantuan sekolah.');
  await user.type(screen.getByLabelText('Alasan koreksi'),'    ');
  expect(screen.getByRole('button',{name:'Simpan koreksi'})).toBeDisabled();
 });
});
