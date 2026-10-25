"""Prepare bounded exports entirely before returning bytes to the browser."""
import csv,io,unicodedata
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException
from backend.app.models import Request
from backend.app.requests.service import iso
from backend.app.audit.service import record
from backend.app.reports.schemas import ReportRow,ReportFilters
from backend.app.reports.service import report_query,report_rows,effective_filters

COLUMNS=('nomor_permohonan','judul','status','dinas_utama','dinas_terlibat','diajukan_wib','diperbarui_wib','prediksi_dinas','confidence','versi_model')
WIB=timezone(timedelta(hours=7))

@dataclass(frozen=True)
class CsvArtifact:
    content:bytes
    filename:str
    generated_at:str

def safe_csv_cell(value:str)->str:
    index=0
    while index<len(value) and (value[index].isspace() or unicodedata.category(value[index])=='Cc' or value[index]=='\ufeff'):
        index+=1
    if value.startswith(('\t','\r','\n')) or (index<len(value) and value[index] in '=+-@'):
        return "'"+value
    return value

def wib_time(value:str|None)->str:
    if not value:return ''
    moment=datetime.fromisoformat(value)
    if moment.tzinfo is None:moment=moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(WIB).isoformat(sep=' ',timespec='seconds')

def encode_csv(rows:list[ReportRow],*,include_classification:bool=True)->bytes:
    buffer=io.StringIO(newline='');writer=csv.writer(buffer,lineterminator='\r\n')
    writer.writerow(COLUMNS if include_classification else COLUMNS[:7])
    for row in rows:
        prediction=row.classification
        values=[row.reference,row.title,row.status,row.primary_agency.name if row.primary_agency else '', '; '.join(a.name for a in row.agencies),wib_time(row.created_at),wib_time(row.updated_at),prediction.predicted_agency_code if prediction else '',prediction.confidence if prediction else '',prediction.model_version if prediction else '']
        if not include_classification:values=values[:7]
        writer.writerow([safe_csv_cell(value) if isinstance(value,str) else value for value in values])
    return buffer.getvalue().encode('utf-8-sig')

def read_export_rows(db,actor,filters:ReportFilters,*,limit:int=5000)->list[ReportRow]:
    statement=report_query(actor,filters)
    ids=db.scalars(statement.with_only_columns(Request.id).order_by(Request.created_at.desc(),Request.id.desc()).limit(limit+1)).all()
    if len(ids)>limit:raise HTTPException(413,'Hasil melebihi 5.000 permohonan. Persempit filter sebelum mengunduh CSV.')
    if not ids:return []
    return report_rows(db,statement.where(Request.id.in_(ids)),offset=0,limit=limit,include_classification=actor.role=='admin')

def prepare_export(db,actor,filters:ReportFilters,generated_at:datetime)->CsvArtifact:
    filters=effective_filters(actor,filters)
    rows=read_export_rows(db,actor,filters)
    content=encode_csv(rows,include_classification=actor.role=='admin')
    moment=generated_at.astimezone(timezone.utc).replace(tzinfo=None) if generated_at.tzinfo else generated_at
    generated=iso(moment)
    record(db,actor.id,'report.export_prepared','report',0,{'filters':filters.model_dump(mode='json'),'count':len(rows),'generated_at':generated})
    db.commit()
    return CsvArtifact(content=content,filename='sgwa-laporan-'+moment.strftime('%Y%m%d-%H%M%S')+'.csv',generated_at=generated)
