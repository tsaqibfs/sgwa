import type {DownloadFile} from './client';
import type {Status} from './types';

export type ReportFilterDraft={date_from:string;date_to:string;status:string;agency_id:string};
export type ReportFilters={date_from:string|null;date_to:string|null;status:Status|null;agency_id:number|null};
export type AgencyRef={id:number;name:string};
export type ReportRow={id:number;reference:string;title:string;status:Status;created_at:string;updated_at:string;primary_agency:AgencyRef|null;agencies:AgencyRef[];classification:{predicted_agency_code:string;confidence:number;model_version:string}|null};
export type ReportSummary={total:number;by_status:Record<Status,number>;completed_count:number;completion_rate:number|null;overdue_count:number;average_completed_hours:number|null};
export type ReportResponse={filters:ReportFilters;generated_at:string;page:number;page_size:number;total:number;summary:ReportSummary;items:ReportRow[]};

export function defaultReportFilters(now:Date):ReportFilterDraft{
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Jakarta',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const values=Object.fromEntries(parts.map(part=>[part.type,part.value]));
 return {date_from:`${values.year}-${values.month}-01`,date_to:`${values.year}-${values.month}-${values.day}`,status:'',agency_id:''};
}

export function reportSearch(filters:ReportFilterDraft,page?:number):string{
 const params=new URLSearchParams();
 for(const key of ['date_from','date_to','status','agency_id'] as const)if(filters[key])params.set(key,filters[key]);
 if(page!==undefined){params.set('page',String(page));params.set('page_size','20')}
 return params.toString();
}

export function saveReportFile(file:DownloadFile):void{
 const url=URL.createObjectURL(file.blob),anchor=document.createElement('a');
 try{anchor.href=url;anchor.download=file.filename;document.body.appendChild(anchor);anchor.click()}
 finally{anchor.remove();URL.revokeObjectURL(url)}
}
