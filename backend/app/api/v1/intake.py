from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.intake_application import IntakeApplication, ApplicationCompleteness, FieldProvenance
from app.models.case import Case, CaseStatus, CasePriority
from app.schemas.intake_application import (
    IntakeApplicationCreate,
    IntakeApplicationUpdate,
    IntakeApplicationResponse,
    DemoIdentityResponse,
    AiIntakeExtractionRequest,
    AiIntakeExtractionResponse,
)
from app.api.deps import get_current_user
from app.services.identity_provider import get_identity_provider, DISCLAIMER_NOTICE
from app.services.ai_intake_mapper import (
    calculate_application_completeness,
    extract_entities_from_spoken_transcript,
)
from app.services.case_workflow import generate_tracking_id
from app.realtime.connection_manager import manager
from app.realtime.events import RealtimeEventType
from app.utils import now_utc

router = APIRouter()


@router.get("/demo-identities")
def list_demo_identities():
    """
    Returns available fictional demo identity records for testing.
    Explicitly labeled as DEMO IDENTITY DATA.
    """
    provider = get_identity_provider()
    records = provider.list_demo_records()
    return {
        "is_demo_data": True,
        "disclaimer": DISCLAIMER_NOTICE,
        "total": len(records),
        "records": records,
    }


@router.post("/demo-lookup")
def demo_identity_lookup(
    phone_number: str = Query(..., description="Caller phone number (DEMO ONLY)")
):
    """
    Demonstrates intake lookup flow:
    caller phone -> demo identity provider -> fictional NID -> fictional applicant profile -> DBLA fields
    
    SAFETY NOTICE:
    DO NOT claim that a real public API can derive a person's NID from an arbitrary phone number.
    DO NOT fabricate government integration.
    Clearly labeled as DEMO IDENTITY DATA.
    """
    provider = get_identity_provider()
    profile = provider.lookup_by_phone(phone_number)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No demo identity record found matching '{phone_number}'. "
                   f"Note: This is simulated demo data only; real SIM cards do not expose citizen NID."
        )
    return profile


@router.post("/extract-ai", response_model=AiIntakeExtractionResponse)
def ai_assisted_intake_extraction(
    req: AiIntakeExtractionRequest
):
    """
    Maps raw spoken answers into validated DBLA structured fields:
    raw spoken answer -> structured extraction -> validated field -> source/provenance
    
    Safety constraints:
    - Never hallucinates or invents missing fields.
    - Missing information remains null / unknown.
    - Computes application completeness (COMPLETE, PARTIALLY_COMPLETE, MISSING_REQUIRED_INFORMATION).
    """
    extracted, provenances = extract_entities_from_spoken_transcript(
        transcript=req.raw_transcript,
        caller_phone=req.caller_phone
    )

    status_val, score, missing, follow_ups = calculate_application_completeness(extracted)

    return AiIntakeExtractionResponse(
        extracted_fields=extracted,
        field_provenances=provenances,
        completeness_status=status_val,
        completeness_score=score,
        missing_required_fields=missing,
        follow_up_questions=follow_ups,
        disclaimer="AI-assisted advisory extraction only. Automated verification is prohibited."
    )


@router.post("/applications", response_model=IntakeApplicationResponse)
async def create_intake_application(
    app_in: IntakeApplicationCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Creates and persists a structured DBLA legal aid application in the authoritative database.
    Calculates completeness score and links to a parent case.
    """
    app_dict = app_in.model_dump()
    field_provenances = app_dict.pop("field_provenances", None) or {}

    # Calculate completeness
    status_val, score, missing, follow_ups = calculate_application_completeness(app_dict)

    tracking_id = generate_tracking_id(db)

    # 1. Create linked parent Case record
    parent_case = Case(
        tracking_id=tracking_id,
        title=app_in.case_title,
        title_bn=app_in.case_title,
        description=app_in.grievance_description,
        description_bn=app_in.grievance_description_bn,
        legal_category=app_in.legal_category,
        status=CaseStatus.PENDING_HUMAN_REVIEW,
        priority=CasePriority.HIGH if app_in.is_below_poverty_line and app_in.total_dependents > 2 else CasePriority.MEDIUM,
        applicant_name=app_in.applicant_name,
        applicant_phone=app_in.phone_number,
        applicant_nid=app_in.nid_number,
        applicant_nid_verified=app_in.nid_verified,
        applicant_income_bdt=app_in.monthly_income_bdt,
        applicant_gender=app_in.gender,
        district=app_in.present_district,
        upazila=app_in.present_upazila,
        intake_channel=app_in.intake_channel,
        version=1,
    )
    db.add(parent_case)
    db.commit()
    db.refresh(parent_case)

    # 2. Create IntakeApplication
    application = IntakeApplication(
        case_id=parent_case.id,
        tracking_id=tracking_id,
        completeness_status=status_val,
        completeness_score=score,
        missing_required_fields=missing,
        follow_up_questions=follow_ups,
        field_provenances=field_provenances,
        is_demo_identity=field_provenances.get("nid_number", {}).get("source") == FieldProvenance.MOCK_IDENTITY,
        **app_dict
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Realtime notification to DLAO queue
    await manager.broadcast_event(
        event_type=RealtimeEventType.CASE_CREATED,
        payload={
            "case_id": parent_case.id,
            "tracking_id": parent_case.tracking_id,
            "title": parent_case.title,
            "status": parent_case.status,
            "priority": parent_case.priority,
            "district": parent_case.district,
            "completeness_status": status_val,
        },
        actor={"user_id": current_user.id if current_user else None, "name": current_user.full_name if current_user else "System", "role": current_user.role if current_user else "citizen"},
    )

    return application


@router.get("/applications/{application_id}", response_model=IntakeApplicationResponse)
def get_intake_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single DBLA intake application with completeness score and field provenances.
    """
    app_record = db.query(IntakeApplication).filter(IntakeApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Intake application not found")
    return app_record


@router.get("/applications", response_model=List[IntakeApplicationResponse])
def list_intake_applications(
    completeness: Optional[str] = Query(None, description="Filter by completeness status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List structured legal aid applications.
    """
    query = db.query(IntakeApplication)
    if completeness:
        query = query.filter(IntakeApplication.completeness_status == completeness)
    return query.order_by(IntakeApplication.id.desc()).limit(50).all()
