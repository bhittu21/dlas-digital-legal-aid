import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AuditAction:
    CASE_CREATED = "CASE_CREATED"
    AI_INTAKE_COMPLETED = "AI_INTAKE_COMPLETED"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    CASE_VERIFIED = "CASE_VERIFIED"
    REQUESTED_INFORMATION = "REQUESTED_INFORMATION"
    CASE_REJECTED = "CASE_REJECTED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    LAWYER_ASSIGNED = "LAWYER_ASSIGNED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_ARCHIVED = "CASE_ARCHIVED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_name = Column(String(255), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    previous_state = Column(String(100), nullable=True)
    new_state = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    case = relationship("Case", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_logs")
