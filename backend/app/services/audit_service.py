import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


def record_audit_log(
    db: Session,
    case_id: Optional[int],
    actor_name: str,
    actor_role: str,
    action: str,
    actor_id: Optional[int] = None,
    previous_state: Optional[str] = None,
    new_state: Optional[str] = None,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None,
    commit: bool = False,
) -> AuditLog:
    """
    Persist an immutable audit log entry in the authoritative database.
    """
    audit = AuditLog(
        case_id=case_id,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action=action,
        previous_state=previous_state,
        new_state=new_state,
        notes=notes,
        ip_address=ip_address,
        timestamp=datetime.datetime.utcnow(),
    )
    db.add(audit)
    if commit:
        db.commit()
        db.refresh(audit)
    return audit
