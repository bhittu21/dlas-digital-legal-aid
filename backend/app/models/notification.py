import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType:
    INFO = "INFO"
    STATUS_CHANGED = "STATUS_CHANGED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    LAWYER_ASSIGNED = "LAWYER_ASSIGNED"
    URGENT_ALERT = "URGENT_ALERT"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    title_bn = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    message_bn = Column(Text, nullable=True)
    type = Column(String(50), nullable=False, default=NotificationType.INFO)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    case = relationship("Case", back_populates="notifications")
