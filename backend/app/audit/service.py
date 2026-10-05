from sqlalchemy.orm import Session
from backend.app.models import AuditLog


def record(session: Session,actor_id: int|None,action: str,entity_type: str,entity_id: int,changes: dict):
    session.add(AuditLog(actor_id=actor_id,action=action,entity_type=entity_type,entity_id=entity_id,changes=changes))
