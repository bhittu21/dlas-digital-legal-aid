from typing import Optional, List
import datetime
from pydantic import BaseModel, Field
from app.schemas.auth import UserResponse


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    title_bn: Optional[str] = None
    description: str = Field(..., min_length=10)
    description_bn: Optional[str] = None
    legal_category: str = "CIVIL_GENERAL"
    priority: str = "MEDIUM"

    applicant_name: str = Field(..., min_length=2, max_length=255)
    applicant_phone: str = Field(..., min_length=7, max_length=50)
    applicant_nid: Optional[str] = None
    applicant_income_bdt: Optional[float] = None
    applicant_gender: Optional[str] = None
    district: str = Field(..., min_length=2, max_length=100)
    upazila: Optional[str] = None

    intake_channel: str = "WEB"
    audio_recording_url: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_urgency_score: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    title_bn: Optional[str] = None
    description: Optional[str] = None
    description_bn: Optional[str] = None
    legal_category: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_phone: Optional[str] = None
    applicant_nid: Optional[str] = None
    applicant_income_bdt: Optional[float] = None
    district: Optional[str] = None
    upazila: Optional[str] = None


class CaseVerifyRequest(BaseModel):
    notes: str = Field(..., min_length=3, description="Mandatory DLAO verification assessment")
    priority: Optional[str] = None
    route_to_panel_queue: bool = True


class CaseRequestInfoRequest(BaseModel):
    info_needed: str = Field(..., min_length=5, description="Specific details requested from applicant")


class CaseRejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Statutory justification for rejection")


class CasePriorityRequest(BaseModel):
    priority: str = Field(..., description="LOW, MEDIUM, HIGH, EMERGENCY")
    reason: str = Field(..., min_length=3, description="Reason for priority adjustment")


class CaseAssignRequest(BaseModel):
    lawyer_id: int = Field(..., description="ID of the panel advocate to assign")
    notes: Optional[str] = None


class CaseArchiveRequest(BaseModel):
    authorization: bool = Field(..., description="Must explicitly confirm human authorization")
    reason: str = Field(..., min_length=5, description="Reason for archival/deletion")


class CaseResponse(BaseModel):
    id: int
    tracking_id: str
    title: str
    title_bn: Optional[str] = None
    description: str
    description_bn: Optional[str] = None
    legal_category: str
    status: str
    priority: str

    applicant_name: str
    applicant_phone: str
    applicant_nid: Optional[str] = None
    applicant_nid_verified: bool
    applicant_income_bdt: Optional[float] = None
    applicant_gender: Optional[str] = None
    district: str
    upazila: Optional[str] = None

    intake_channel: str
    audio_recording_url: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_urgency_score: Optional[str] = None

    verification_notes: Optional[str] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime.datetime] = None

    assigned_lawyer_id: Optional[int] = None
    assigned_at: Optional[datetime.datetime] = None

    archived: bool
    archived_at: Optional[datetime.datetime] = None
    archived_by_id: Optional[int] = None

    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    size: int
    total_pages: int
