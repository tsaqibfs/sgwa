import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,vi,afterEach} from 'vitest';
import {Theme} from '@radix-ui/themes';
import {WorkflowRoutes} from '../pages/WorkflowRoutes';
afterEach(()=>vi.unstubAllGlobals());
it('tujuan nonaktif yang masih terpilih dapat dihapus dari rute',async()=>{
 const rules=[{source_code:'perizinan',source_name:'Perizinan',active:true,agency_ids:[1,2]}];
 const agencies=[{id:1,code:'perizinan',name:'Perizinan',active:true,sla_days:3},{id:2,code:'pajak',name:'Pajak',active:false,sla_days:3}];
 const fetch=vi.fn().mockImplementation(async(url:string,opts:RequestInit={})=>new Response(JSON.stringify(opts.method==='PUT'?{agency_ids:[1]}:url.includes('/workflow/routes')?rules:agencies)));vi.stubGlobal('fetch',fetch);
 render(<Theme><WorkflowRoutes/></Theme>);
 const checkbox=await screen.findByRole('checkbox',{name:/Pajak/});await waitFor(()=>expect(checkbox).toBeChecked());
 await userEvent.click(checkbox);await userEvent.click(screen.getByRole('button',{name:'Simpan rute'}));
 await screen.findByText('Rute tersimpan.');
 const saved=fetch.mock.calls.find(([,options])=>options?.method==='PUT');expect(JSON.parse(saved![1].body as string).agency_ids).toEqual([1]);
});
