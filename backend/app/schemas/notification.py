from typing import Optional
import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    case_id: Optional[int] = None
    title: str
    title_bn: Optional[str] = None
    message: str
    message_bn: Optional[str] = None
    type: str
    is_read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True
