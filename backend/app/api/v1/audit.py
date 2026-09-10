from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.api.deps import require_dlao

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
def list_system_audit_logs(
    case_id: Optional[int] = Query(None, description="Filter by case ID"),
    action: Optional[str] = Query(None, description="Filter by audit action"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    Retrieve authoritative audit trail logs. Restricted to DLAO officers and Admins.
    """
    query = db.query(AuditLog)
    if case_id:
        query = query.filter(AuditLog.case_id == case_id)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
