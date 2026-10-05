import { render,screen,fireEvent,waitFor } from '@testing-library/react';
import { describe,it,expect,vi } from 'vitest';
import { Theme } from '@radix-ui/themes';
import { RequestForm } from '../components/RequestForm';

describe('Pengajuan permohonan',()=>{
 it('menolak teks pendek dan mempertahankan input setelah server gagal',async()=>{
  const submit=vi.fn().mockRejectedValue(new Error('Layanan belum tersedia'));
  render(<Theme><RequestForm onSubmit={submit}/></Theme>);
  fireEvent.change(screen.getByLabelText('Judul permohonan'),{target:{value:'KTP'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim permohonan'}));
  expect(submit).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Judul permohonan'),{target:{value:'Pengurusan KTP'}});
  fireEvent.change(screen.getByLabelText('Ceritakan kebutuhan Anda'),{target:{value:'Saya ingin mengurus KTP yang hilang dan kartu keluarga.'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim permohonan'}));
  await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('Layanan belum tersedia'));
  expect(screen.getByLabelText('Judul permohonan')).toHaveValue('Pengurusan KTP');
 });
 it('mencegah pengiriman ganda selama menunggu respons',async()=>{
  let finish!:()=>void;
  const submit=vi.fn(()=>new Promise<void>(resolve=>{finish=resolve}));
  render(<Theme><RequestForm onSubmit={submit}/></Theme>);
  fireEvent.change(screen.getByLabelText('Judul permohonan'),{target:{value:'Pengurusan KTP'}});
  fireEvent.change(screen.getByLabelText('Ceritakan kebutuhan Anda'),{target:{value:'Saya ingin mengurus KTP yang hilang dan kartu keluarga.'}});
  const button=screen.getByRole('button',{name:'Kirim permohonan'});
  fireEvent.click(button);fireEvent.click(button);
  expect(submit).toHaveBeenCalledTimes(1);
  expect(button).toBeDisabled();finish();
  await waitFor(()=>expect(button).not.toBeDisabled());
 });
});
