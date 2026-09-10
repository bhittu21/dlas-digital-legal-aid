import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CaseStatus:
    NEW = "NEW"
    AI_INTAKE = "AI_INTAKE"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    VERIFIED = "VERIFIED"
    PANEL_LAWYER_QUEUE = "PANEL_LAWYER_QUEUE"
    LAWYER_REVIEW = "LAWYER_REVIEW"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

    ALL_STATUSES = [
        NEW,
        AI_INTAKE,
        PENDING_HUMAN_REVIEW,
        VERIFIED,
        PANEL_LAWYER_QUEUE,
        LAWYER_REVIEW,
        NEEDS_INFORMATION,
        REJECTED,
        ARCHIVED,
    ]


class CasePriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"

    ALL_PRIORITIES = [LOW, MEDIUM, HIGH, EMERGENCY]


class LegalCategory:
    FAMILY_MATRIMONIAL = "FAMILY_MATRIMONIAL"
    LAND_PROPERTY = "LAND_PROPERTY"
    DOMESTIC_VIOLENCE_DOWRY = "DOMESTIC_VIOLENCE_DOWRY"
    LABOUR_EMPLOYMENT = "LABOUR_EMPLOYMENT"
    CRIMINAL_DEFENSE_BAIL = "CRIMINAL_DEFENSE_BAIL"
    CIVIL_GENERAL = "CIVIL_GENERAL"

    ALL_CATEGORIES = [
        FAMILY_MATRIMONIAL,
        LAND_PROPERTY,
        DOMESTIC_VIOLENCE_DOWRY,
        LABOUR_EMPLOYMENT,
        CRIMINAL_DEFENSE_BAIL,
        CIVIL_GENERAL,
    ]


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    title_bn = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    description_bn = Column(Text, nullable=True)

    legal_category = Column(String(100), nullable=False, default=LegalCategory.CIVIL_GENERAL, index=True)
    status = Column(String(50), nullable=False, default=CaseStatus.NEW, index=True)
    priority = Column(String(50), nullable=False, default=CasePriority.MEDIUM, index=True)

    # Applicant Details
    applicant_name = Column(String(255), nullable=False)
    applicant_phone = Column(String(50), nullable=False, index=True)
    applicant_nid = Column(String(50), nullable=True, index=True)
    applicant_nid_verified = Column(Boolean, default=False)
    applicant_income_bdt = Column(Float, nullable=True)
    applicant_gender = Column(String(20), nullable=True)
    district = Column(String(100), nullable=False, index=True)
    upazila = Column(String(100), nullable=True)

    # Ingestion & AI Metadata
    intake_channel = Column(String(50), default="WEB")  # WEB, PHONE_VOICE, WALK_IN, SMS
    audio_recording_url = Column(String(500), nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_urgency_score = Column(String(50), nullable=True)

    # Verification (Human DLAO Only)
    verification_notes = Column(Text, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Panel Lawyer Assignment
    assigned_lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Archival / Deletion (Human DLAO Only)
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    archived_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Optimistic Concurrency Control
    version = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    verified_by = relationship("User", foreign_keys=[verified_by_id], back_populates="verified_cases")
    assigned_lawyer = relationship("User", foreign_keys=[assigned_lawyer_id], back_populates="assigned_cases")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan", order_by="desc(AuditLog.timestamp)")
    notifications = relationship("Notification", back_populates="case", cascade="all, delete-orphan")
