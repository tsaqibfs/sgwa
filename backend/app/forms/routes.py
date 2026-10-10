from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import Agency,ServiceForm,ServiceFormVersion,User,utcnow
from backend.app.auth.dependencies import get_current_user,require_role
from backend.app.audit.service import record
from backend.app.forms.schemas import FormCreate,DraftUpdate,Publish,FormActive,FormSchema
from backend.app.forms.service import locked_form,latest_version,form_out

router=APIRouter(prefix='/service-forms',tags=['Formulir layanan'])


@router.get('')
def listing(actor:User=Depends(get_current_user),db:Session=Depends(get_session)):
    query=select(ServiceForm).join(Agency,Agency.id==ServiceForm.agency_id).order_by(ServiceForm.id.desc())
    if actor.role!='admin':query=query.where(ServiceForm.active.is_(True),ServiceForm.current_version>0,Agency.active.is_(True))
    return [form_out(db,form,actor.role=='admin') for form in db.scalars(query)]


@router.get('/{form_id}')
def detail(form_id:int,actor:User=Depends(get_current_user),db:Session=Depends(get_session)):
    form=db.get(ServiceForm,form_id)
    agency=db.get(Agency,form.agency_id) if form else None
    if not form or actor.role!='admin' and (not form.active or not form.current_version or not agency.active):raise HTTPException(404,'Formulir tidak ditemukan.')
    return form_out(db,form,actor.role=='admin')


@router.post('',status_code=201)
def create(payload:FormCreate,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    agency=db.scalar(select(Agency).where(Agency.id==payload.agency_id).with_for_update())
    if not agency or not agency.active:raise HTTPException(422,'Pilih dinas aktif.')
    form=ServiceForm(agency_id=agency.id,title=payload.title.strip());db.add(form);db.flush()
    db.add(ServiceFormVersion(form_id=form.id,version=1,title=form.title,schema_json=FormSchema(fields=payload.fields).model_dump(),created_by=actor.id))
    record(db,actor.id,'form.created','service_form',form.id,{'agency_id':agency.id});db.commit()
    return form_out(db,form,True)


@router.patch('/{form_id}/draft')
def edit(form_id:int,payload:DraftUpdate,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    form,agency=locked_form(db,form_id);latest=latest_version(db,form,lock=True)
    if latest.version!=payload.expected_version:raise HTTPException(409,'Versi formulir sudah berubah.')
    latest=ServiceFormVersion(form_id=form.id,version=latest.version+1,title=form.title,schema_json={},created_by=actor.id);db.add(latest)
    latest.schema_json=FormSchema(fields=payload.fields).model_dump()
    if payload.title is not None:form.title=payload.title.strip()
    latest.title=form.title
    record(db,actor.id,'form.draft_updated','service_form',form.id,{'version':latest.version});db.commit()
    return form_out(db,form,True)


@router.post('/{form_id}/publish')
def publish(form_id:int,payload:Publish,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    form,agency=locked_form(db,form_id);latest=latest_version(db,form,lock=True)
    if not agency.active or not form.active:raise HTTPException(422,'Dinas dan formulir harus aktif.')
    if latest.version!=payload.expected_version or latest.state!='draft':raise HTTPException(409,'Draft telah berubah atau sudah dipublikasikan.')
    FormSchema.model_validate(latest.schema_json)
    latest.state='published';latest.published_at=utcnow();form.current_version=latest.version
    record(db,actor.id,'form.published','service_form',form.id,{'version':latest.version});db.commit()
    return form_out(db,form,True)


@router.patch('/{form_id}')
def activate(form_id:int,payload:FormActive,actor:User=Depends(require_role('admin')),db:Session=Depends(get_session)):
    form,_=locked_form(db,form_id);form.active=payload.active
    record(db,actor.id,'form.active_changed','service_form',form.id,{'active':form.active});db.commit()
    return form_out(db,form,True)
