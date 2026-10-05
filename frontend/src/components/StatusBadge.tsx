import type {Status} from '../api/types';
export const statusLabel:Record<Status,string>={pending:'Menunggu',processing:'Diproses',escalated:'Perlu review',approved:'Disetujui',rejected:'Ditolak'};
export function StatusBadge({status}:{status:Status}){return <span className={'status status-'+status}><i/>{statusLabel[status]}</span>}
