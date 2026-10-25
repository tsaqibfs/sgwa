import type {Agency,RequestItem,Status} from '../api/types';
import {statusLabel} from './StatusBadge';
export const date=(iso:string)=>new Intl.DateTimeFormat('id-ID',{timeZone:'Asia/Jakarta',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(iso));
function readableNote(note:string,agencies:Pick<Agency,'id'|'name'>[]){
 return note.replace(/^Dinas #(\d+): (pending|processing|approved|rejected|escalated)\.\s*/,(_prefix,id:string,status:string)=>`${agencies.find(agency=>agency.id===Number(id))?.name??'Petugas dinas'}: ${statusLabel[status as Status]}. `);
}
export function RequestTimeline({events,agencies=[]}:{events:RequestItem['events'];agencies?:Pick<Agency,'id'|'name'>[]}){return <ol className="timeline">{events?.map(event=><li key={event.id}><span className="timeline-dot"/><div><strong>{statusLabel[event.to_status]}</strong><p>{readableNote(event.note,agencies)}</p><time>{date(event.created_at)} WIB</time></div></li>)}</ol>}
