from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.models import Agency


def active_agency(db: Session,agency_id: int) -> Agency:
    agency=db.get(Agency,agency_id)
    if not agency or not agency.active:
        raise HTTPException(422,'Dinas tidak tersedia atau tidak aktif.')
    return agency


def commit_unique(db: Session):
    try:
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Kode dinas atau email sudah digunakan.')


def agency_out(agency: Agency):
    return {key:getattr(agency,key) for key in ['id','code','name','description','active']}
