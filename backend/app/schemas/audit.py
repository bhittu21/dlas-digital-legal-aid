from typing import Optional
import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    case_id: Optional[int] = None
    actor_id: Optional[int] = None
    actor_name: str
    actor_role: str
    action: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
