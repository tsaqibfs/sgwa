import type {RequestItem} from '../api/types';
import {statusLabel} from './StatusBadge';
export const date=(iso:string)=>new Intl.DateTimeFormat('id-ID',{timeZone:'Asia/Jakarta',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(iso));
export function RequestTimeline({events}:{events:RequestItem['events']}){return <ol className="timeline">{events?.map(event=><li key={event.id}><span className="timeline-dot"/><div><strong>{statusLabel[event.to_status]}</strong><p>{event.note}</p><time>{date(event.created_at)} WIB</time></div></li>)}</ol>}
