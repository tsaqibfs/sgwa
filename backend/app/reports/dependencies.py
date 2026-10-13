from fastapi import Depends,Request
from sqlalchemy.orm import Session
from backend.app.models import User
from backend.app.auth.dependencies import get_current_user,require_role
from backend.app.reports.session import get_report_session

def get_report_actor(request:Request,db:Session=Depends(get_report_session))->User:
    """Reuse existing auth/roles within the report's one RR connection."""
    actor=get_current_user(request,session=db)
    return require_role('citizen','staff','admin')(actor)
