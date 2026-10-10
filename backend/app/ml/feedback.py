"""Explicit human corrections, isolated from service routing and decisions."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import User,Request,Agency,ClassificationResult,MLFeedback,MLFeedbackHead,utcnow
from backend.app.audit.service import record
from backend.app.requests.service import iso
from ml.build_dataset import canonical_hash
from ml.text import text_hash


def locked_admin(db,actor):
    actor=db.scalar(select(User).where(User.id==actor.id).with_for_update().execution_options(populate_existing=True))
    if not actor or not actor.active:raise HTTPException(401,'Sesi berakhir.')
    if actor.role!='admin':raise HTTPException(403,'Hanya admin dapat mengelola koreksi ML.')
    return actor


def locked_head(db,request_id):
    item=db.scalar(select(Request).where(Request.id==request_id).with_for_update().execution_options(populate_existing=True))
    if not item:raise HTTPException(404,'Permohonan tidak ditemukan.')
    head=db.scalar(select(MLFeedbackHead).where(MLFeedbackHead.request_id==request_id).with_for_update().execution_options(populate_existing=True))
    if head is None:
        head=MLFeedbackHead(request_id=request_id,revision=0);db.add(head);db.flush()
    return item,head


def create_feedback(db: Session,actor: User,request_id: int,payload) -> MLFeedback:
    actor=locked_admin(db,actor)
    digest=canonical_hash({'request_id':request_id,**payload.model_dump()})
    existing=db.scalar(select(MLFeedback).where(MLFeedback.created_by==actor.id,MLFeedback.idempotency_key==payload.idempotency_key).with_for_update())
    if existing:
        if existing.payload_hash!=digest:raise HTTPException(409,'Kunci koreksi telah dipakai untuk input berbeda.')
        db.commit();return existing
    item,head=locked_head(db,request_id)
    if head.revision!=payload.expected_revision:raise HTTPException(409,'Koreksi telah berubah. Muat ulang dan tinjau revisinya.')
    agency=db.scalar(select(Agency).where(Agency.code==payload.corrected_code,Agency.active.is_(True)).with_for_update())
    if not agency:raise HTTPException(422,'Kelas koreksi harus instansi aktif.')
    prediction=db.scalar(select(ClassificationResult).where(ClassificationResult.request_id==request_id))
    if not prediction:raise HTTPException(422,'Permohonan belum memiliki prediksi awal.')
    if head.current_feedback_id:
        previous=db.get(MLFeedback,head.current_feedback_id)
        previous.status='superseded'
    row=MLFeedback(request_id=request_id,revision=head.revision+1,original_text=item.title+' '+item.description,
        original_prediction={'predicted_agency_code':prediction.predicted_agency_code,'probabilities':prediction.probabilities,
                             'confidence':prediction.confidence,'needs_review':prediction.needs_review,'model_version':prediction.model_version},
        training_text=payload.training_text,text_hash=text_hash(payload.training_text),corrected_code=payload.corrected_code,
        provenance=payload.provenance,family_key=payload.family_key,reason=payload.reason,created_by=actor.id,
        idempotency_key=payload.idempotency_key,payload_hash=digest,status='pending')
    db.add(row);db.flush();head.revision=row.revision;head.current_feedback_id=row.id
    record(db,actor.id,'ml.feedback_created','request',request_id,{'feedback_id':row.id,'revision':row.revision,'corrected_code':row.corrected_code,'provenance':row.provenance})
    db.commit();return row


def review_feedback(db: Session,actor: User,feedback_id: int,payload) -> MLFeedback:
    actor=locked_admin(db,actor)
    row=db.get(MLFeedback,feedback_id)
    if not row:raise HTTPException(404,'Koreksi tidak ditemukan.')
    _,head=locked_head(db,row.request_id)
    row=db.scalar(select(MLFeedback).where(MLFeedback.id==feedback_id).with_for_update().execution_options(populate_existing=True))
    if head.revision!=payload.expected_revision or head.current_feedback_id!=row.id or row.status!='pending':
        raise HTTPException(409,'Revisi ini telah berubah atau sudah diperiksa.')
    row.status=payload.decision;row.reviewed_by=actor.id;row.reviewed_at=utcnow();row.review_note=payload.note
    record(db,actor.id,'ml.feedback_reviewed','request',row.request_id,{'feedback_id':row.id,'revision':row.revision,'decision':row.status,'note':row.review_note})
    db.commit();return row


def feedback_out(db,row):
    head=db.get(MLFeedbackHead,row.request_id)
    return {key:getattr(row,key) for key in ('id','request_id','revision','original_text','original_prediction','training_text',
        'text_hash','corrected_code','provenance','family_key','reason','status','created_by','reviewed_by','review_note')} | {
        'created_at':iso(row.created_at),'reviewed_at':iso(row.reviewed_at),'current_revision':head.revision if head else 0,
        'is_current':bool(head and head.current_feedback_id==row.id)}
