import {render,screen,waitFor,cleanup,act} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';
import {Theme} from '@radix-ui/themes';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {Reports} from './Reports';
import {ApiError} from '../api/client';
import type {ReportResponse} from '../api/reports';
const state=vi.hoisted(()=>({user:{id:1,name:'Warga',email:'warga@test.id',role:'citizen' as 'citizen'|'staff'|'admin',agency_id:null as number|null,active:true},file:vi.fn(),save:vi.fn()}));
vi.mock('../auth/AuthProvider',()=>({useAuth:()=>({user:state.user})}));
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),apiFile:state.file}));
vi.mock('../api/reports',async()=>({...await vi.importActual('../api/reports'),saveReportFile:state.save}));

function body(path:string):ReportResponse{
 const query=new URL(path,'http://localhost').searchParams;
 return {filters:{date_from:query.get('date_from'),date_to:query.get('date_to'),status:query.get('status') as 'approved'|null,agency_id:query.has('agency_id')?Number(query.get('agency_id')):null},generated_at:'2026-10-13T01:00:00Z',page:Number(query.get('page')??1),page_size:20,total:21,summary:{total:21,by_status:{pending:20,processing:0,escalated:0,approved:1,rejected:0},completed_count:1,completion_rate:1/21,overdue_count:0,average_completed_hours:2},items:[{id:1,reference:'REPORT-1',title:query.get('status')==='approved'?'Hasil disetujui':'Hasil awal',status:'approved',created_at:'2026-10-13T01:00:00Z',updated_at:'2026-10-13T03:00:00Z',primary_agency:{id:1,name:'Dukcapil'},agencies:[{id:1,name:'Dukcapil'}],classification:null}]};
}
let fetchMock:ReturnType<typeof vi.fn>;
beforeEach(()=>{
 state.user.role='citizen';state.user.agency_id=null;state.file.mockReset();state.save.mockReset();state.file.mockResolvedValue({blob:new Blob(['csv']),filename:'sgwa-laporan.csv',generatedAt:null});
 fetchMock=vi.fn((path:string)=>Promise.resolve(new Response(JSON.stringify(path.includes('/agencies')?[{id:1,name:'Dukcapil',active:true},{id:2,name:'Kesehatan',active:false}]:body(path)))));vi.stubGlobal('fetch',fetchMock);
});
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
function mount(){return render(<Theme><MemoryRouter><Reports/></MemoryRouter></Theme>)}
async function ready(){await waitFor(()=>expect(screen.getByRole('button',{name:'Unduh CSV'})).toBeEnabled())}

it('applies filters separately from drafts and resets pagination',async()=>{
 const user=userEvent.setup();mount();await ready();await user.selectOptions(screen.getByLabelText('Status permohonan'),'approved');
 await user.click(screen.getByRole('button',{name:'Unduh CSV'}));expect(state.file.mock.calls[0][0]).not.toContain('status=approved');expect(state.file.mock.calls[0][0]).not.toContain('page=');await ready();
 await user.click(screen.getByRole('button',{name:'Berikutnya'}));await waitFor(()=>expect(fetchMock.mock.calls.some(c=>String(c[0]).includes('page=2'))).toBe(true));await ready();
 await user.click(screen.getByRole('button',{name:'Terapkan filter'}));await ready();expect(screen.getByText('Hasil disetujui')).toBeVisible();await user.click(screen.getByRole('button',{name:'Unduh CSV'}));expect(state.file.mock.calls.at(-1)![0]).toContain('status=approved');
 await ready();await user.click(screen.getByRole('button',{name:'Reset'}));await ready();expect(screen.getByLabelText('Status permohonan')).toHaveValue('');expect(screen.getByText('Hasil awal')).toBeVisible();
});
it('does not pair stale table with new filter export while response is delayed',async()=>{
 const user=userEvent.setup();mount();await ready();let finish!:(value:Response)=>void;
 fetchMock.mockImplementation((path:string)=>path.includes('status=approved')?new Promise<Response>(r=>{finish=r}):Promise.resolve(new Response(JSON.stringify(body(path)))));
 await user.selectOptions(screen.getByLabelText('Status permohonan'),'approved');await user.click(screen.getByRole('button',{name:'Terapkan filter'}));expect(screen.getByRole('button',{name:'Unduh CSV'})).toBeDisabled();expect(state.file).not.toHaveBeenCalled();
 expect(screen.queryByText('Hasil awal')).not.toBeInTheDocument();await act(async()=>finish(new Response(JSON.stringify(body('/reports?status=approved&page=1')))));
 // Echo does not match the date filters, so it must stay disabled.
 expect(screen.getByRole('button',{name:'Unduh CSV'})).toBeDisabled();
});
it('guards duplicate download and preserves applied filters on session error',async()=>{
 const user=userEvent.setup();mount();await ready();let finish!:(value:unknown)=>void;state.file.mockImplementationOnce(()=>new Promise(r=>{finish=r}));
 await user.dblClick(screen.getByRole('button',{name:'Unduh CSV'}));expect(state.file).toHaveBeenCalledOnce();expect(screen.getByRole('button',{name:'Terapkan filter'})).toBeDisabled();
 await act(async()=>finish({blob:new Blob(['csv']),filename:'sgwa-laporan.csv',generatedAt:null}));await ready();state.file.mockRejectedValueOnce(new ApiError(401,'Sesi berakhir'));
 await user.click(screen.getByRole('button',{name:'Unduh CSV'}));await expect(screen.findByRole('alert')).resolves.toHaveTextContent('Sesi berakhir');expect(state.save).toHaveBeenCalledOnce();expect(screen.getByText('Hasil awal')).toBeVisible();
});
it('shows empty results and null metrics without hiding export header download',async()=>{
 fetchMock.mockImplementation((path:string)=>Promise.resolve(new Response(JSON.stringify(path.includes('/agencies')?[]:{...body(path),total:0,items:[],summary:{...body(path).summary,total:0,completed_count:0,completion_rate:null,average_completed_hours:null}}))));
 mount();await ready();expect(screen.getByText('Tidak ada permohonan sesuai filter.')).toBeVisible();expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2);
});
it('keeps staff agency fixed and includes inactive agency options for admin',async()=>{
 state.user.role='staff';state.user.agency_id=1;mount();await ready();expect(screen.getByLabelText('Dinas dalam laporan')).toBeDisabled();expect(screen.getByLabelText('Dinas dalam laporan')).toHaveValue('1');cleanup();state.user.role='admin';state.user.agency_id=null;mount();await ready();expect(screen.getByRole('option',{name:'Kesehatan (nonaktif)'})).toBeInTheDocument();
});
