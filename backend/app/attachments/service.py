import os
import re
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.models import RequestAttachment, Request, RequestWorkflow, Agency, User, RequestEvent, utcnow
from backend.app.audit.service import record

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    return clean[:200] if clean else 'dokumen'


def get_upload_dir() -> Path:
    settings = get_settings()
    path = settings.upload_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(
    db: Session,
    actor: User,
    file: UploadFile,
    agency_id: int | None = None,
    request_id: int | None = None,
    field_key: str | None = None,
    description: str | None = None
) -> RequestAttachment:
    original_name = file.filename or 'dokumen'
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(422, f'Format file tidak didukung. Gunakan format: {", ".join(sorted(ALLOWED_EXTENSIONS))}')

    content = file.file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(422, 'File tidak boleh kosong.')
    if size > MAX_FILE_SIZE:
        raise HTTPException(422, 'Ukuran file melebihi batas maksimal 10 MB.')

    if agency_id:
        agency = db.get(Agency, agency_id)
        if not agency or not agency.active:
            raise HTTPException(422, 'Dinas tidak valid atau tidak aktif.')

    if request_id:
        req = db.get(Request, request_id)
        if not req:
            raise HTTPException(404, 'Permohonan tidak ditemukan.')
        if actor.role == 'citizen' and req.citizen_id != actor.id:
            raise HTTPException(403, 'Akses permohonan ditolak.')
        if actor.role == 'staff':
            is_assigned = db.scalar(
                select(RequestWorkflow.id).where(
                    RequestWorkflow.request_id == req.id,
                    RequestWorkflow.agency_id == actor.agency_id
                )
            )
            if not is_assigned:
                raise HTTPException(403, 'Bukan permohonan dinas Anda.')
            if agency_id and agency_id != actor.agency_id:
                raise HTTPException(403, 'Staf hanya dapat mengunggah berkas untuk dinasnya sendiri.')
            if not agency_id:
                agency_id = actor.agency_id

    stored_name = f"{uuid.uuid4().hex}{ext}"
    upload_path = get_upload_dir() / stored_name
    upload_path.write_bytes(content)

    attachment = RequestAttachment(
        request_id=request_id,
        agency_id=agency_id,
        uploaded_by=actor.id,
        filename=sanitize_filename(original_name),
        stored_name=stored_name,
        content_type=file.content_type or 'application/octet-stream',
        size_bytes=size,
        field_key=field_key,
        description=(description or '').strip() or None
    )
    db.add(attachment)
    db.flush()

    if request_id:
        agency_name = db.get(Agency, agency_id).name if agency_id else 'Umum'
        db.add(RequestEvent(
            request_id=request_id,
            actor_id=actor.id,
            event_type='attachment_added',
            from_status=None,
            to_status=None,
            note=f"Berkas pendukung ditambahkan ({attachment.filename}) untuk {agency_name}."
        ))
        record(db, actor.id, 'request.attachment_added', 'request_attachment', attachment.id, {
            'request_id': request_id,
            'agency_id': agency_id,
            'filename': attachment.filename
        })

    db.commit()
    db.refresh(attachment)
    return attachment


def check_attachment_access(db: Session, actor: User, attachment: RequestAttachment) -> bool:
    if actor.role == 'admin':
        return True
    if attachment.uploaded_by == actor.id:
        return True
    if not attachment.request_id:
        return False
    req = db.get(Request, attachment.request_id)
    if not req:
        return False
    if actor.role == 'citizen':
        return req.citizen_id == actor.id
    if actor.role == 'staff':
        # staff can see attachments for their agency or assigned workflow
        if attachment.agency_id == actor.agency_id:
            return True
        is_assigned = db.scalar(
            select(RequestWorkflow.id).where(
                RequestWorkflow.request_id == req.id,
                RequestWorkflow.agency_id == actor.agency_id
            )
        )
        return bool(is_assigned)
    return False


def get_request_attachments(db: Session, actor: User, request_id: int) -> list[dict]:
    req = db.get(Request, request_id)
    if not req:
        raise HTTPException(404, 'Permohonan tidak ditemukan.')
    if actor.role == 'citizen' and req.citizen_id != actor.id:
        raise HTTPException(403, 'Akses permohonan ditolak.')
    if actor.role == 'staff':
        is_assigned = db.scalar(
            select(RequestWorkflow.id).where(
                RequestWorkflow.request_id == req.id,
                RequestWorkflow.agency_id == actor.agency_id
            )
        )
        if not is_assigned:
            raise HTTPException(403, 'Akses permohonan ditolak.')

    items = db.scalars(
        select(RequestAttachment)
        .where(RequestAttachment.request_id == request_id)
        .order_by(RequestAttachment.id.asc())
    ).all()

    result = []
    for item in items:
        if not check_attachment_access(db, actor, item):
            continue
        agency = db.get(Agency, item.agency_id) if item.agency_id else None
        uploader = db.get(User, item.uploaded_by)
        result.append(serialize_attachment(item, agency, uploader))
    return result


def serialize_attachment(item: RequestAttachment, agency: Agency | None = None, uploader: User | None = None) -> dict:
    return {
        'id': item.id,
        'request_id': item.request_id,
        'agency_id': item.agency_id,
        'agency_name': agency.name if agency else 'Umum / Semua Dinas',
        'agency_code': agency.code if agency else None,
        'uploaded_by': item.uploaded_by,
        'uploader_name': uploader.name if uploader else 'Sistem',
        'filename': item.filename,
        'content_type': item.content_type,
        'size_bytes': item.size_bytes,
        'field_key': item.field_key,
        'description': item.description,
        'created_at': item.created_at.isoformat() + 'Z' if item.created_at else None
    }


def delete_attachment(db: Session, actor: User, attachment_id: int):
    item = db.get(RequestAttachment, attachment_id)
    if not item:
        raise HTTPException(404, 'Berkas tidak ditemukan.')
    if actor.role != 'admin' and item.uploaded_by != actor.id:
        raise HTTPException(403, 'Hanya pengunggah atau admin yang dapat menghapus berkas.')

    if item.request_id:
        req = db.get(Request, item.request_id)
        if req and req.status in ('approved', 'rejected') and actor.role != 'admin':
            raise HTTPException(409, 'Tidak dapat menghapus berkas dari permohonan yang sudah selesai.')

    # Remove file from disk
    file_path = get_upload_dir() / item.stored_name
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass

    req_id = item.request_id
    filename = item.filename
    db.delete(item)

    if req_id:
        db.add(RequestEvent(
            request_id=req_id,
            actor_id=actor.id,
            event_type='attachment_removed',
            from_status=None,
            to_status=None,
            note=f"Berkas pendukung dihapus: {filename}."
        ))
        record(db, actor.id, 'request.attachment_removed', 'request_attachment', attachment_id, {
            'request_id': req_id,
            'filename': filename
        })
    db.commit()


def link_attachments_to_request(db: Session, actor: User, request_id: int, attachment_ids: list[int], default_agency_id: int | None = None):
    if not attachment_ids:
        return
    attachments = db.scalars(
        select(RequestAttachment).where(
            RequestAttachment.id.in_(attachment_ids),
            RequestAttachment.uploaded_by == actor.id,
            RequestAttachment.request_id.is_(None)
        )
    ).all()
    for att in attachments:
        att.request_id = request_id
        if not att.agency_id and default_agency_id:
            att.agency_id = default_agency_id
    db.flush()
