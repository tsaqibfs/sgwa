from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User,Agency
from backend.app.auth.dependencies import get_current_user,require_role
from backend.app.auth.schemas import UserOut
from backend.app.auth.service import hash_password
from backend.app.agencies.schemas import AgencyCreate,AgencyUpdate,StaffCreate,StaffUpdate
from backend.app.agencies.service import active_agency,commit_unique,agency_out
from backend.app.audit.service import record

router=APIRouter(tags=['Administrasi'])


@router.get('/agencies')
def agencies(actor: User=Depends(get_current_user),db: Session=Depends(get_session)):
    return [agency_out(a) for a in db.scalars(select(Agency).order_by(Agency.name)).all()]


@router.post('/agencies',status_code=201)
def create_agency(payload: AgencyCreate,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    agency=Agency(**payload.model_dump());db.add(agency)
    try:
        db.flush()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Kode dinas sudah digunakan.')
    record(db,actor.id,'agency.created','agency',agency.id,payload.model_dump());commit_unique(db)
    return agency_out(agency)


@router.patch('/agencies/{agency_id}')
def change_agency(agency_id: int,payload: AgencyUpdate,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    agency=db.get(Agency,agency_id)
    if not agency:
        raise HTTPException(404,'Dinas tidak ditemukan.')
    changes=payload.model_dump(exclude_unset=True)
    if any(v is None for v in changes.values()):
        raise HTTPException(422,'Nilai dinas tidak boleh kosong.')
    for key,value in changes.items():
        setattr(agency,key,value)
    record(db,actor.id,'agency.updated','agency',agency.id,changes);commit_unique(db)
    return agency_out(agency)


@router.get('/staff',response_model=list[UserOut])
def staff(actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    return db.scalars(select(User).where(User.role=='staff').order_by(User.name)).all()


@router.post('/staff',status_code=201,response_model=UserOut)
def create_staff(payload: StaffCreate,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    active_agency(db,payload.agency_id)
    user=User(name=payload.name,email=str(payload.email),password_hash=hash_password(payload.password),role='staff',agency_id=payload.agency_id)
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Email sudah terdaftar.')
    record(db,actor.id,'staff.created','user',user.id,{'agency_id':user.agency_id});commit_unique(db)
    return user


@router.patch('/staff/{user_id}',response_model=UserOut)
def change_staff(user_id: int,payload: StaffUpdate,actor: User=Depends(require_role('admin')),db: Session=Depends(get_session)):
    user=db.get(User,user_id)
    if not user or user.role!='staff':
        raise HTTPException(404,'Staf tidak ditemukan.')
    changes=payload.model_dump(exclude_unset=True)
    if any(v is None for v in changes.values()):
        raise HTTPException(422,'Nilai staf tidak boleh kosong.')
    if 'agency_id' in changes:
        active_agency(db,changes['agency_id'])
    for key,value in changes.items():
        setattr(user,key,value)
    record(db,actor.id,'staff.updated','user',user.id,changes);commit_unique(db)
    return user
