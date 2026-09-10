import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole:
    DLAO_OFFICER = "dlao_officer"
    PANEL_LAWYER = "panel_lawyer"
    APPLICANT = "applicant"
    ADMIN = "admin"
    SYSTEM_AI = "system_ai"

    ALL_ROLES = [DLAO_OFFICER, PANEL_LAWYER, APPLICANT, ADMIN, SYSTEM_AI]
    HUMAN_ROLES = [DLAO_OFFICER, PANEL_LAWYER, APPLICANT, ADMIN]
    VERIFIER_ROLES = [DLAO_OFFICER, ADMIN]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    full_name_bn = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default=UserRole.APPLICANT, index=True)
    phone_number = Column(String(50), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    specialization = Column(String(100), nullable=True)  # e.g., Land, Family, Criminal, Labour
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    verified_cases = relationship("Case", foreign_keys="Case.verified_by_id", back_populates="verified_by")
    assigned_cases = relationship("Case", foreign_keys="Case.assigned_lawyer_id", back_populates="assigned_lawyer")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
