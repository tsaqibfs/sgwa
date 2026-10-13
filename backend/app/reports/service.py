from datetime import datetime,time,timedelta,timezone
from fastapi import HTTPException
from sqlalchemy import select,func,text
from sqlalchemy.orm import Session
from backend.app.models import User,Agency,Request,RequestWorkflow,ClassificationResult
from backend.app.requests.service import scoped_query,iso
from backend.app.reports.schemas import ReportFilters,ReportQuery,ReportRow,AgencyRef,ReportClassification,ReportSummary,ReportResponse,STATUSES

def effective_filters(actor:User,filters:ReportFilters)->ReportFilters:
    if actor.role not in ('citizen','staff','admin'):raise HTTPException(403,'Anda tidak memiliki akses ke laporan.')
    result=ReportFilters(**{key:value for key,value in filters.model_dump().items() if key in ReportFilters.model_fields})
    if actor.role=='staff':
        if result.agency_id is not None and result.agency_id!=actor.agency_id:
            raise HTTPException(403,'Laporan staf terbatas pada dinas akunnya.')
        result.agency_id=actor.agency_id
    return result

def utc_bounds(filters:ReportFilters)->tuple[datetime|None,datetime|None]:
    start=datetime.combine(filters.date_from,time.min)-timedelta(hours=7) if filters.date_from else None
    end=datetime.combine(filters.date_to,time.max)-timedelta(hours=7)+timedelta(microseconds=1) if filters.date_to else None
    return start,end

def report_query(actor:User,filters:ReportFilters):
    filters=effective_filters(actor,filters)
    query=scoped_query(actor)
    start,end=utc_bounds(filters)
    if start is not None:query=query.where(Request.created_at>=start)
    if end is not None:query=query.where(Request.created_at<end)
    if filters.status:query=query.where(Request.status==filters.status)
    if filters.agency_id:
        query=query.where(select(RequestWorkflow.id).where(RequestWorkflow.request_id==Request.id,RequestWorkflow.agency_id==filters.agency_id).exists())
    return query

def report_rows(db:Session,statement,*,offset:int,limit:int)->list[ReportRow]:
    items=db.scalars(statement.order_by(Request.created_at.desc(),Request.id.desc()).offset(offset).limit(limit)).all()
    if not items:return []
    ids=[row.id for row in items]
    primary_ids={row.assigned_agency_id for row in items if row.assigned_agency_id is not None}
    primary={row.id:AgencyRef(id=row.id,name=row.name) for row in db.scalars(select(Agency).where(Agency.id.in_(primary_ids)))}
    tasks={rid:[] for rid in ids}
    for rid,agency in db.execute(select(RequestWorkflow.request_id,Agency).join(Agency,Agency.id==RequestWorkflow.agency_id).where(RequestWorkflow.request_id.in_(ids)).order_by(Agency.name,Agency.id)):
        tasks[rid].append(AgencyRef(id=agency.id,name=agency.name))
    predictions={row.request_id:ReportClassification(predicted_agency_code=row.predicted_agency_code,confidence=row.confidence,model_version=row.model_version) for row in db.scalars(select(ClassificationResult).where(ClassificationResult.request_id.in_(ids)))}
    return [ReportRow(id=row.id,reference=row.reference,title=row.title,status=row.status,created_at=iso(row.created_at),updated_at=iso(row.updated_at),primary_agency=primary.get(row.assigned_agency_id),agencies=tasks[row.id],classification=predictions.get(row.id)) for row in items]

def read_report(db:Session,actor:User,query:ReportQuery,generated_at:datetime)->ReportResponse:
    filters=effective_filters(actor,query)
    statement=report_query(actor,filters);scoped=statement.subquery()
    by_status={status:0 for status in STATUSES}
    by_status.update(dict(db.execute(select(scoped.c.status,func.count()).group_by(scoped.c.status)).all()))
    total=sum(by_status.values());completed=by_status['approved']+by_status['rejected']
    average=db.scalar(select(func.avg(func.timestampdiff(text('SECOND'),scoped.c.created_at,scoped.c.updated_at)/3600)).where(scoped.c.status.in_(['approved','rejected']),scoped.c.updated_at>=scoped.c.created_at))
    moment=generated_at.astimezone(timezone.utc).replace(tzinfo=None) if generated_at.tzinfo else generated_at
    overdue_tasks=select(RequestWorkflow.id).where(RequestWorkflow.request_id==scoped.c.id,RequestWorkflow.status.in_(['pending','processing']),RequestWorkflow.due_at<moment)
    if filters.agency_id:overdue_tasks=overdue_tasks.where(RequestWorkflow.agency_id==filters.agency_id)
    overdue=db.scalar(select(func.count()).select_from(scoped).where(scoped.c.status.not_in(['approved','rejected']),overdue_tasks.exists()))
    summary=ReportSummary(total=total,by_status=by_status,completed_count=completed,completion_rate=completed/total if total else None,overdue_count=overdue or 0,average_completed_hours=float(average) if average is not None else None)
    return ReportResponse(filters=filters,generated_at=iso(moment),page=query.page,page_size=query.page_size,total=total,summary=summary,items=report_rows(db,statement,offset=(query.page-1)*query.page_size,limit=query.page_size))
