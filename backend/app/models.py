from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, JSON, Boolean, DateTime, Integer,UniqueConstraint,CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Agency(Base):
    __tablename__ = 'agencies'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default='')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sla_days: Mapped[int] = mapped_column(Integer,default=3,server_default='3')


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='citizen')
    agency_id: Mapped[int | None] = mapped_column(ForeignKey('agencies.id'))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(500))
    session_version: Mapped[int] = mapped_column(Integer, default=1, server_default='1')


class Request(Base):
    __tablename__ = 'requests'
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    assigned_agency_id: Mapped[int | None] = mapped_column(ForeignKey('agencies.id'), index=True)
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    form_version_id: Mapped[int | None] = mapped_column(ForeignKey('service_form_versions.id'))
    form_answers: Mapped[dict | None] = mapped_column(JSON)


class ClassificationResult(Base):
    __tablename__ = 'classification_results'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), unique=True)
    predicted_agency_code: Mapped[str] = mapped_column(String(50))
    probabilities: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float]
    needs_review: Mapped[bool] = mapped_column(Boolean)
    model_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RequestWorkflow(Base):
    __tablename__='request_workflows'
    __table_args__=(UniqueConstraint('request_id','agency_id',name='uq_request_agency'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    request_id: Mapped[int]=mapped_column(ForeignKey('requests.id'),index=True)
    agency_id: Mapped[int]=mapped_column(ForeignKey('agencies.id'),index=True)
    status: Mapped[str]=mapped_column(String(20),default='pending',index=True)
    version: Mapped[int]=mapped_column(Integer,default=1)
    due_at: Mapped[datetime|None]=mapped_column(DateTime,index=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime)
    decision_note: Mapped[str]=mapped_column(Text,default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)


class WorkflowRoute(Base):
    __tablename__='workflow_routes'
    __table_args__=(UniqueConstraint('source_code','agency_id',name='uq_route_destination'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    source_code: Mapped[str]=mapped_column(ForeignKey('agencies.code'),index=True)
    agency_id: Mapped[int]=mapped_column(ForeignKey('agencies.id'))


class RequestEvent(Base):
    __tablename__ = 'request_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    event_type: Mapped[str] = mapped_column(String(30))
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int]
    changes: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ServiceForm(Base):
    __tablename__ = 'service_forms'
    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey('agencies.id'), index=True)
    title: Mapped[str] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_version: Mapped[int] = mapped_column(Integer, default=0)


class ServiceFormVersion(Base):
    __tablename__ = 'service_form_versions'
    __table_args__ = (UniqueConstraint('form_id', 'version', name='uq_form_version'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey('service_forms.id'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(150))
    schema_json: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(20), default='draft')
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)


class Notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = (UniqueConstraint('user_id', 'event_key', name='uq_notification_event'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    event_key: Mapped[str] = mapped_column(String(150))
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(150))
    request_id: Mapped[int | None] = mapped_column(ForeignKey('requests.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)


class ResultDocument(Base):
    __tablename__ = 'result_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), unique=True)
    number: Mapped[str] = mapped_column(String(60), unique=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MockCheck(Base):
    __tablename__ = 'mock_checks'
    __table_args__ = (UniqueConstraint('actor_id', 'idempotency_key', name='uq_mock_actor_key'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    check_type: Mapped[str] = mapped_column(String(40))
    outcome: Mapped[str] = mapped_column(String(30))
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    payload: Mapped[dict] = mapped_column(JSON)
    idempotency_key: Mapped[str] = mapped_column(String(100))


class MLFeedback(Base):
    __tablename__ = 'ml_feedback'
    __table_args__ = (UniqueConstraint('request_id','revision',name='uq_ml_feedback_revision'),
                     UniqueConstraint('created_by','idempotency_key',name='uq_ml_feedback_key'),
                     CheckConstraint("status IN ('pending','verified','rejected','superseded')",name='ck_ml_feedback_status'),
                     CheckConstraint("provenance IN ('synthetic_demo','real')",name='ck_ml_feedback_provenance'))
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'),index=True)
    revision: Mapped[int] = mapped_column(Integer)
    original_text: Mapped[str] = mapped_column(Text)
    original_prediction: Mapped[dict] = mapped_column(JSON)
    training_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64),index=True)
    corrected_code: Mapped[str] = mapped_column(ForeignKey('agencies.code'))
    provenance: Mapped[str] = mapped_column(String(20))
    family_key: Mapped[str|None] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20),default='pending',index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime,default=utcnow)
    reviewed_by: Mapped[int|None] = mapped_column(ForeignKey('users.id'))
    reviewed_at: Mapped[datetime|None] = mapped_column(DateTime)
    review_note: Mapped[str|None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    payload_hash: Mapped[str] = mapped_column(String(64))


class MLFeedbackHead(Base):
    __tablename__ = 'ml_feedback_heads'
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'),primary_key=True)
    revision: Mapped[int] = mapped_column(Integer,default=0)
    current_feedback_id: Mapped[int|None] = mapped_column(ForeignKey('ml_feedback.id',name='fk_ml_head_current'))


class MLModelVersion(Base):
    __tablename__ = 'ml_model_versions'
    __table_args__ = (CheckConstraint("state IN ('ready','failed')",name='ck_ml_model_state'),)
    id: Mapped[str] = mapped_column(String(80),primary_key=True)
    state: Mapped[str] = mapped_column(String(20))
    relative_path: Mapped[str] = mapped_column(String(150))
    model_hash: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON)
    evaluation_json: Mapped[dict] = mapped_column(JSON)
    feedback_manifest: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=utcnow)
    registered_by: Mapped[int|None] = mapped_column(ForeignKey('users.id'))
    failure_reason: Mapped[str|None] = mapped_column(Text)


class MLActiveModel(Base):
    __tablename__ = 'ml_active_model'
    __table_args__ = (CheckConstraint('id=1',name='ck_ml_singleton'),)
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=False)
    model_version_id: Mapped[str|None] = mapped_column(ForeignKey('ml_model_versions.id'))
    revision: Mapped[int] = mapped_column(Integer,default=0)


class MLActivation(Base):
    __tablename__ = 'ml_activations'
    id: Mapped[int] = mapped_column(primary_key=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey('ml_model_versions.id'))
    previous_version_id: Mapped[str|None] = mapped_column(ForeignKey('ml_model_versions.id'))
    actor_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'))
    reason: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime,default=utcnow)


class RequestAttachment(Base):
    __tablename__ = 'request_attachments'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey('requests.id'), index=True)
    agency_id: Mapped[int | None] = mapped_column(ForeignKey('agencies.id'), index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    field_key: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

