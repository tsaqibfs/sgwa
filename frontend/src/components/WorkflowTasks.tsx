import type {WorkflowTask} from '../api/types';
import {StatusBadge} from './StatusBadge';
import {date} from './RequestTimeline';
export function WorkflowTasks({tasks,ownAgency,emptyMessage='Dinas tujuan ditetapkan setelah pemeriksaan admin.'}:{tasks:WorkflowTask[];ownAgency?:number|null;emptyMessage?:string}){
 return <section className="panel workflow-panel"><div className="section-heading"><div><h2>Progres tiap dinas</h2><p>Permohonan selesai setelah seluruh dinas menyetujui, atau keputusan review admin.</p></div></div>{tasks.length?tasks.map(task=><article className="workflow-task" key={task.id}><div><strong>{task.agency_name}{task.agency_id===ownAgency&&<span className="own-task">Dinas Anda</span>}</strong><p>{task.due_at?'Tenggat: '+date(task.due_at)+' WIB':'Tugas historis tanpa tenggat'}{task.overdue&&<span className="overdue-label"> · SLA terlewati</span>}</p>{task.decision_note&&<p className="task-note">{task.decision_note}</p>}</div><StatusBadge status={task.status}/></article>):<p className="subtle">{emptyMessage}</p>}</section>;
}
