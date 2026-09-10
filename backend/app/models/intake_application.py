import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils import now_utc


class ApplicationCompleteness:
    COMPLETE = "COMPLETE"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    MISSING_REQUIRED_INFORMATION = "MISSING_REQUIRED_INFORMATION"

    ALL_STATUSES = [COMPLETE, PARTIALLY_COMPLETE, MISSING_REQUIRED_INFORMATION]


class FieldProvenance:
    CALLER_REPORTED = "CALLER_REPORTED"
    AI_EXTRACTED = "AI_EXTRACTED"
    MOCK_IDENTITY = "MOCK_IDENTITY"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"

    ALL_SOURCES = [
        CALLER_REPORTED,
        AI_EXTRACTED,
        MOCK_IDENTITY,
        HUMAN_VERIFIED,
        SYSTEM_DERIVED,
    ]


class IntakeApplication(Base):
    """
    Structured Legal Aid Application Model modeled after the official
    National Legal Aid Services Organization (NLASO) DBLA Online Application Form
    (https://db.nlaso.gov.bd/Pages/OnlineApplications.aspx).
    
    Stores complete citizen profile, socio-economic eligibility, adverse parties,
    grievance details, and field-by-field provenance tracking.
    """
    __tablename__ = "intake_applications"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    tracking_id = Column(String(50), unique=True, index=True, nullable=False)

    # 1. Applicant Profile
    applicant_name = Column(String(255), nullable=False)
    applicant_name_bn = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)  # MALE, FEMALE, OTHER
    date_of_birth = Column(String(50), nullable=True)  # YYYY-MM-DD
    age = Column(Integer, nullable=True)
    marital_status = Column(String(50), nullable=True)  # MARRIED, UNMARRIED, WIDOWED, DIVORCED, SEPARATED
    religion = Column(String(50), nullable=True)  # ISLAM, HINDUISM, BUDDHISM, CHRISTIANITY, OTHER

    # 2. Contact Information
    phone_number = Column(String(50), nullable=False, index=True)
    alternate_phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # 3. National Identification (NID)
    nid_number = Column(String(50), nullable=True, index=True)
    nid_type = Column(String(50), nullable=True)  # SMART_10, LEGACY_17, BIRTH_REGISTRATION
    nid_verified = Column(Boolean, default=False)
    nid_verification_source = Column(String(50), default="MOCK_IDENTITY")

    # 4. Occupation & Livelihood
    occupation = Column(String(100), nullable=True)
    occupation_bn = Column(String(100), nullable=True)
    employer_name = Column(String(255), nullable=True)
    designation = Column(String(100), nullable=True)

    # 5. Household Income & Statutory Eligibility
    monthly_income_bdt = Column(Float, nullable=True)
    annual_income_bdt = Column(Float, nullable=True)
    income_source = Column(String(150), nullable=True)
    is_below_poverty_line = Column(Boolean, default=True)

    # 6. Educational Attainment
    education_level = Column(String(50), nullable=True)  # ILLITERATE, PRIMARY, SECONDARY, HIGHER_SECONDARY, GRADUATE, POST_GRADUATE

    # 7. Dependants & Household Composition
    total_dependents = Column(Integer, default=0)
    minor_children_count = Column(Integer, default=0)
    elderly_dependents_count = Column(Integer, default=0)
    dependent_details = Column(Text, nullable=True)

    # 8. Parents
    father_name = Column(String(255), nullable=True)
    father_name_bn = Column(String(255), nullable=True)
    mother_name = Column(String(255), nullable=True)
    mother_name_bn = Column(String(255), nullable=True)

    # 9. Spouse Information
    spouse_name = Column(String(255), nullable=True)
    spouse_name_bn = Column(String(255), nullable=True)
    spouse_occupation = Column(String(100), nullable=True)

    # 10. Current (Present) Address
    present_division = Column(String(100), nullable=True)
    present_district = Column(String(100), nullable=False)
    present_upazila = Column(String(100), nullable=True)
    present_union_ward = Column(String(100), nullable=True)
    present_village_road = Column(String(255), nullable=True)
    present_post_code = Column(String(20), nullable=True)

    # 11. Permanent Address
    is_permanent_same_as_present = Column(Boolean, default=True)
    permanent_division = Column(String(100), nullable=True)
    permanent_district = Column(String(100), nullable=True)
    permanent_upazila = Column(String(100), nullable=True)
    permanent_union_ward = Column(String(100), nullable=True)
    permanent_village_road = Column(String(255), nullable=True)
    permanent_post_code = Column(String(20), nullable=True)

    # 12. Representative / Authorized Agent (if applicant cannot file personally)
    has_representative = Column(Boolean, default=False)
    representative_name = Column(String(255), nullable=True)
    representative_relation = Column(String(100), nullable=True)
    representative_phone = Column(String(50), nullable=True)
    representative_address = Column(Text, nullable=True)

    # 13. Opposing Party (Adverse Party)
    opposing_party_name = Column(String(255), nullable=True)
    opposing_party_relation = Column(String(100), nullable=True)
    opposing_party_phone = Column(String(50), nullable=True)
    opposing_party_address = Column(Text, nullable=True)

    # 14. Case / Problem Description & Statutory Relief
    legal_category = Column(String(100), nullable=False)
    legal_sub_category = Column(String(150), nullable=True)
    case_title = Column(String(255), nullable=False)
    grievance_description = Column(Text, nullable=False)
    grievance_description_bn = Column(Text, nullable=True)
    relief_sought = Column(Text, nullable=True)
    incident_date = Column(String(50), nullable=True)
    previous_case_filed = Column(Boolean, default=False)
    previous_case_number = Column(String(100), nullable=True)
    court_name = Column(String(150), nullable=True)

    # 15. Field-by-Field Provenance & Audit Metadata
    # Maps field name -> { "source": "CALLER_REPORTED" | "AI_EXTRACTED" | "MOCK_IDENTITY" | ..., "timestamp": "...", "confidence": 1.0 }
    field_provenances = Column(JSON, default=dict)

    # 16. Completeness Evaluation
    completeness_status = Column(String(50), default=ApplicationCompleteness.MISSING_REQUIRED_INFORMATION, index=True)
    completeness_score = Column(Float, default=0.0)
    missing_required_fields = Column(JSON, default=list)
    follow_up_questions = Column(JSON, default=list)

    # Ingestion Metadata
    intake_channel = Column(String(50), default="WEB")  # WEB, PHONE_VOICE, WALK_IN
    raw_spoken_transcript = Column(Text, nullable=True)
    is_demo_identity = Column(Boolean, default=False)

    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    # Relationship to parent case
    case = relationship("Case", backref="intake_application")
