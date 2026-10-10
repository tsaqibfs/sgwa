from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, JSON, Boolean, DateTime, Integer,UniqueConstraint
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
