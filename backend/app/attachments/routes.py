from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import RequestAttachment, Agency, User
from backend.app.auth.dependencies import get_current_user
from backend.app.attachments.service import (
    save_upload,
    get_request_attachments,
    check_attachment_access,
    delete_attachment,
    serialize_attachment,
    get_upload_dir
)

router = APIRouter(tags=['Berkas pendukung'])


@router.post('/attachments/upload')
def upload_attachment(
    file: UploadFile = File(...),
    agency_id: int | None = Form(None),
    request_id: int | None = Form(None),
    field_key: str | None = Form(None),
    description: str | None = Form(None),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    attachment = save_upload(
        db,
        actor,
        file,
        agency_id=agency_id,
        request_id=request_id,
        field_key=field_key,
        description=description
    )
    agency = db.get(Agency, attachment.agency_id) if attachment.agency_id else None
    return serialize_attachment(attachment, agency, actor)


@router.get('/requests/{request_id}/attachments')
def list_request_attachments(
    request_id: int,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    return get_request_attachments(db, actor, request_id)


@router.post('/requests/{request_id}/attachments')
def upload_request_attachment(
    request_id: int,
    file: UploadFile = File(...),
    agency_id: int | None = Form(None),
    description: str | None = Form(None),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    attachment = save_upload(
        db,
        actor,
        file,
        agency_id=agency_id,
        request_id=request_id,
        description=description
    )
    agency = db.get(Agency, attachment.agency_id) if attachment.agency_id else None
    return serialize_attachment(attachment, agency, actor)


@router.get('/attachments/{attachment_id}/download')
def download_attachment(
    attachment_id: int,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    item = db.get(RequestAttachment, attachment_id)
    if not item:
        raise HTTPException(404, 'Berkas tidak ditemukan.')
    if not check_attachment_access(db, actor, item):
        raise HTTPException(403, 'Akses berkas ditolak.')

    file_path = get_upload_dir() / item.stored_name
    if not file_path.exists():
        raise HTTPException(404, 'File fisik tidak ditemukan pada server.')

    return FileResponse(
        path=str(file_path),
        filename=item.filename,
        media_type=item.content_type,
        content_disposition_type='attachment'
    )


@router.delete('/attachments/{attachment_id}')
def remove_attachment(
    attachment_id: int,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    delete_attachment(db, actor, attachment_id)
    return {'status': 'deleted', 'id': attachment_id}
