from typing import Annotated
from fastapi import APIRouter,Depends,Query,Response
from sqlalchemy.orm import Session
from backend.app.models import User,utcnow
from backend.app.auth.dependencies import require_role
from backend.app.reports.schemas import ReportFilters,ReportQuery,ReportResponse
from backend.app.reports.session import get_report_session
from backend.app.reports.service import read_report
from backend.app.reports.csv_export import prepare_export

router=APIRouter(prefix='/reports',tags=['Laporan layanan'])

@router.get('',response_model=ReportResponse)
def report(filters:Annotated[ReportQuery,Query()],actor:User=Depends(require_role('citizen','staff','admin')),db:Session=Depends(get_report_session)):
    return read_report(db,actor,filters,utcnow())

@router.get('/requests.csv')
def export(filters:Annotated[ReportFilters,Query()],actor:User=Depends(require_role('citizen','staff','admin')),db:Session=Depends(get_report_session)):
    artifact=prepare_export(db,actor,filters,utcnow())
    return Response(content=artifact.content,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{artifact.filename}"','X-Report-Generated-At':artifact.generated_at,'Cache-Control':'no-store'})
