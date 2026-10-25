import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {RequestTimeline} from './RequestTimeline';

const departments=[{id:1,name:'Dinas Kependudukan dan Pencatatan Sipil'}];
it.each([['processing','Diproses'],['approved','Disetujui']] as const)('menampilkan nama dinas dan status umum untuk riwayat %s lama tanpa mengubah sumber', (status,label)=>{
 const events=[{id:1,to_status:status,note:`Dinas #1: ${status}. Informasi tindak lanjut.`,created_at:'2026-10-24T14:00:00Z'}];
 render(<RequestTimeline events={events} agencies={departments}/>);
 expect(screen.getByText(`Dinas Kependudukan dan Pencatatan Sipil: ${label}. Informasi tindak lanjut.`)).toBeVisible();
 expect(screen.queryByText(events[0].note)).not.toBeInTheDocument();
 expect(events[0].note).toBe(`Dinas #1: ${status}. Informasi tindak lanjut.`);
});
it('menggunakan keterangan umum ketika nama dinas historis tidak tersedia',()=>{
 render(<RequestTimeline events={[{id:1,to_status:'approved',note:'Dinas #99: approved. Selesai.',created_at:'2026-10-24T14:00:00Z'}]} agencies={departments}/>);
 expect(screen.getByText('Petugas dinas: Disetujui. Selesai.')).toBeVisible();
});
it('tidak mengganti kata yang ditulis dalam catatan petugas',()=>{
 const note='Catatan petugas menyebut processing dan approved sebagai contoh istilah.';
 render(<RequestTimeline events={[{id:1,to_status:'approved',note,created_at:'2026-10-24T14:00:00Z'}]} agencies={departments}/>);
 expect(screen.getByText(note)).toBeVisible();
});
