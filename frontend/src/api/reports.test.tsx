import {afterEach,it,expect,vi} from 'vitest';
import {defaultReportFilters,reportSearch,saveReportFile} from './reports';
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()});
it('sets default month from WIB rather than host date',()=>{
 expect(defaultReportFilters(new Date('2026-10-31T18:00:00Z'))).toEqual({date_from:'2026-11-01',date_to:'2026-11-01',status:'',agency_id:''});
});
it('omits empty filters and CSV pagination',()=>{
 const filters={date_from:'',date_to:'2026-10-13',status:'approved',agency_id:'2'};
 const listing=new URLSearchParams(reportSearch(filters,2)),csv=new URLSearchParams(reportSearch(filters));
 expect(listing.get('page')).toBe('2');expect(listing.get('page_size')).toBe('20');expect(listing.has('date_from')).toBe(false);expect(csv.has('page')).toBe(false);expect(csv.has('page_size')).toBe(false);expect(csv.get('agency_id')).toBe('2');expect(csv.get('status')).toBe('approved');
});
it('revokes object URL and removes download anchor',()=>{
 const create=vi.fn(()=> 'blob:test'),revoke=vi.fn();const OriginalURL=URL;vi.stubGlobal('URL',class extends OriginalURL{static createObjectURL=create;static revokeObjectURL=revoke});let clicked:HTMLAnchorElement|undefined;
 vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){clicked=this;expect(this.download).toBe('sgwa-laporan.csv');expect(this.href).toBe('blob:test')});
 saveReportFile({blob:new Blob(['header']),filename:'sgwa-laporan.csv',generatedAt:null});expect(clicked).toBeDefined();expect(revoke).toHaveBeenCalledWith('blob:test');expect(document.querySelector('a[download]')).toBeNull();
});
