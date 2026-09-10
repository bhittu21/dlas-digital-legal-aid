from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import datetime


class ProvenanceEntry(BaseModel):
    source: str = Field(..., description="Provenance source: CALLER_REPORTED, AI_EXTRACTED, MOCK_IDENTITY, HUMAN_VERIFIED, SYSTEM_DERIVED")
    timestamp: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class IntakeApplicationBase(BaseModel):
    # Applicant Profile
    applicant_name: str
    applicant_name_bn: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None

    # Contact
    phone_number: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None

    # NID
    nid_number: Optional[str] = None
    nid_type: Optional[str] = None
    nid_verified: bool = False
    nid_verification_source: str = "MOCK_IDENTITY"

    # Occupation & Income
    occupation: Optional[str] = None
    occupation_bn: Optional[str] = None
    employer_name: Optional[str] = None
    designation: Optional[str] = None
    monthly_income_bdt: Optional[float] = None
    annual_income_bdt: Optional[float] = None
    income_source: Optional[str] = None
    is_below_poverty_line: bool = True

    # Education & Dependants
    education_level: Optional[str] = None
    total_dependents: int = 0
    minor_children_count: int = 0
    elderly_dependents_count: int = 0
    dependent_details: Optional[str] = None

    # Family (Parents & Spouse)
    father_name: Optional[str] = None
    father_name_bn: Optional[str] = None
    mother_name: Optional[str] = None
    mother_name_bn: Optional[str] = None
    spouse_name: Optional[str] = None
    spouse_name_bn: Optional[str] = None
    spouse_occupation: Optional[str] = None

    # Addresses
    present_division: Optional[str] = None
    present_district: str
    present_upazila: Optional[str] = None
    present_union_ward: Optional[str] = None
    present_village_road: Optional[str] = None
    present_post_code: Optional[str] = None

    is_permanent_same_as_present: bool = True
    permanent_division: Optional[str] = None
    permanent_district: Optional[str] = None
    permanent_upazila: Optional[str] = None
    permanent_union_ward: Optional[str] = None
    permanent_village_road: Optional[str] = None
    permanent_post_code: Optional[str] = None

    # Representative & Opposing Party
    has_representative: bool = False
    representative_name: Optional[str] = None
    representative_relation: Optional[str] = None
    representative_phone: Optional[str] = None
    representative_address: Optional[str] = None

    opposing_party_name: Optional[str] = None
    opposing_party_relation: Optional[str] = None
    opposing_party_phone: Optional[str] = None
    opposing_party_address: Optional[str] = None

    # Dispute / Case Details
    legal_category: str
    legal_sub_category: Optional[str] = None
    case_title: str
    grievance_description: str
    grievance_description_bn: Optional[str] = None
    relief_sought: Optional[str] = None
    incident_date: Optional[str] = None
    previous_case_filed: bool = False
    previous_case_number: Optional[str] = None
    court_name: Optional[str] = None

    intake_channel: str = "WEB"
    raw_spoken_transcript: Optional[str] = None


class IntakeApplicationCreate(IntakeApplicationBase):
    field_provenances: Optional[Dict[str, Dict[str, Any]]] = None


class IntakeApplicationUpdate(BaseModel):
    # Any field can be updated during manual editing
    applicant_name: Optional[str] = None
    applicant_name_bn: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None
    phone_number: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    nid_number: Optional[str] = None
    nid_type: Optional[str] = None
    nid_verified: Optional[bool] = None
    occupation: Optional[str] = None
    monthly_income_bdt: Optional[float] = None
    present_district: Optional[str] = None
    present_upazila: Optional[str] = None
    opposing_party_name: Optional[str] = None
    opposing_party_relation: Optional[str] = None
    legal_category: Optional[str] = None
    case_title: Optional[str] = None
    grievance_description: Optional[str] = None
    relief_sought: Optional[str] = None
    field_provenances: Optional[Dict[str, Dict[str, Any]]] = None


class IntakeApplicationResponse(IntakeApplicationBase):
    id: int
    case_id: Optional[int] = None
    tracking_id: str
    completeness_status: str
    completeness_score: float
    missing_required_fields: List[str]
    follow_up_questions: List[Dict[str, Any]]
    field_provenances: Dict[str, Any]
    is_demo_identity: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class DemoIdentityResponse(BaseModel):
    is_demo_data: bool = True
    disclaimer: str = "DEMO IDENTITY DATA - NOT A REAL GOVERNMENT REGISTRY INTEGRATION"
    phone_number: str
    applicant_name: str
    applicant_name_bn: str
    nid_number: str
    nid_type: str
    gender: str
    date_of_birth: str
    father_name: str
    father_name_bn: str
    mother_name: str
    mother_name_bn: str
    present_division: str
    present_district: str
    present_upazila: str
    occupation: str
    monthly_income_bdt: float
    education_level: str


class AiIntakeExtractionRequest(BaseModel):
    raw_transcript: str = Field(..., description="Raw spoken conversational transcript from caller")
    caller_phone: Optional[str] = None
    existing_application_id: Optional[int] = None


class AiIntakeExtractionResponse(BaseModel):
    extracted_fields: Dict[str, Any]
    field_provenances: Dict[str, Dict[str, Any]]
    completeness_status: str
    completeness_score: float
    missing_required_fields: List[str]
    follow_up_questions: List[Dict[str, Any]]
    disclaimer: str = "AI-assisted advisory extraction only. Automated verification is prohibited."
