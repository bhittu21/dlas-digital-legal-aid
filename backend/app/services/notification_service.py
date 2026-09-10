import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    case_id: Optional[int] = None,
    title_bn: Optional[str] = None,
    message_bn: Optional[str] = None,
    notification_type: str = NotificationType.INFO,
    commit: bool = False,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        case_id=case_id,
        title=title,
        title_bn=title_bn,
        message=message,
        message_bn=message_bn,
        type=notification_type,
        is_read=False,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    return notification
