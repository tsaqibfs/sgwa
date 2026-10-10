from fastapi import HTTPException
from sqlalchemy import select
from backend.app.models import ServiceForm,ServiceFormVersion,Agency,utcnow
from backend.app.forms.schemas import FormSchema
from backend.app.forms.validation import validate_answers


def locked_form(db,form_id):
    form=db.get(ServiceForm,form_id)
    if not form:raise HTTPException(404,'Formulir tidak ditemukan.')
    agency=db.scalar(select(Agency).where(Agency.id==form.agency_id).with_for_update().execution_options(populate_existing=True))
    form=db.scalar(select(ServiceForm).where(ServiceForm.id==form_id).with_for_update().execution_options(populate_existing=True))
    return form,agency


def latest_version(db,form,lock=False):
    query=select(ServiceFormVersion).where(ServiceFormVersion.form_id==form.id).order_by(ServiceFormVersion.version.desc()).limit(1)
    if lock:query=query.with_for_update().execution_options(populate_existing=True)
    return db.scalar(query)


def version_out(version):
    return None if version is None else {'id':version.id,'version':version.version,'title':version.title,'state':version.state,'schema':version.schema_json}


def form_out(db,form,admin=False):
    published=db.scalar(select(ServiceFormVersion).where(ServiceFormVersion.form_id==form.id,ServiceFormVersion.version==form.current_version,ServiceFormVersion.state=='published'))
    latest=latest_version(db,form) if admin else None
    return {'id':form.id,'title':form.title,'agency_id':form.agency_id,'active':form.active,'current_version':form.current_version,'published':version_out(published),'draft':version_out(latest) if latest and latest.state=='draft' else None}


def resolve_submission_form(db,version_id,answers):
    version=db.get(ServiceFormVersion,version_id)
    if not version:raise HTTPException(422,'Versi formulir tidak ditemukan.')
    form,agency=locked_form(db,version.form_id)
    if not form.active or not agency or not agency.active or version.state!='published' or version.version!=form.current_version:
        raise HTTPException(409,'Formulir telah berubah atau nonaktif. Muat ulang dan tinjau jawaban Anda.')
    clean=validate_answers(FormSchema.model_validate(version.schema_json),answers)
    answers.clear();answers.update(clean)
    return version
