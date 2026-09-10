import pytest
from app.models.case import Case, CaseStatus, CasePriority
from app.models.user import User, UserRole
from app.services.case_workflow import CaseWorkflowService


@pytest.mark.asyncio
async def test_full_successful_lifecycle(db, client, dlao_headers):
    """
    Test complete canonical pipeline:
    NEW -> AI_INTAKE -> PENDING_HUMAN_REVIEW -> VERIFIED -> PANEL_LAWYER_QUEUE -> LAWYER_REVIEW
    """
    # 1. Create NEW case via API
    case_payload = {
        "title": "Inheritance Land Dispute in Manikganj",
        "title_bn": "মানিকগঞ্জে পৈতৃক জমি বণ্টন সংক্রান্ত বিরোধ",
        "description": "Ancestral agricultural land of 50 decimals illegally occupied by cousins.",
        "legal_category": "LAND_PROPERTY",
        "priority": "MEDIUM",
        "applicant_name": "Abul Kashem",
        "applicant_phone": "+8801711223399",
        "applicant_nid": "1234567890",
        "applicant_income_bdt": 8000.0,
        "district": "Dhaka",
        "upazila": "Manikganj Sadar",
        "intake_channel": "WEB",
    }
    create_res = client.post("/api/v1/cases", json=case_payload, headers=dlao_headers)
    assert create_res.status_code == 201
    case_data = create_res.json()
    case_id = case_data["id"]
    assert case_data["status"] == CaseStatus.NEW

    # 2. Transition to AI_INTAKE
    dlao_user = db.query(User).filter(User.role == UserRole.DLAO_OFFICER).first()
    case_ai = await CaseWorkflowService.transition_to_ai_intake(db, case_id, dlao_user)
    assert case_ai.status == CaseStatus.AI_INTAKE

    # 3. AI completes intake -> PENDING_HUMAN_REVIEW
    ai_user = db.query(User).filter(User.role == UserRole.SYSTEM_AI).first()
    case_pending = await CaseWorkflowService.complete_ai_intake(
        db=db,
        case_id=case_id,
        ai_summary="AI extraction: Title partition issue. Financial eligibility met.",
        urgency_score="HIGH",
        actor=ai_user
    )
    assert case_pending.status == CaseStatus.PENDING_HUMAN_REVIEW
    assert case_pending.ai_urgency_score == "HIGH"

    # 4. Human DLAO verifies case -> PANEL_LAWYER_QUEUE
    verify_payload = {
        "notes": "Verified CS/RS Khatian copies and applicant insolvency declaration.",
        "priority": "HIGH",
        "route_to_panel_queue": True
    }
    verify_res = client.post(f"/api/v1/cases/{case_id}/verify", json=verify_payload, headers=dlao_headers)
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["status"] == CaseStatus.PANEL_LAWYER_QUEUE
    assert verified_data["priority"] == "HIGH"
    assert verified_data["verified_by_id"] == dlao_user.id

    # 5. DLAO assigns Panel Lawyer -> LAWYER_REVIEW
    lawyer = db.query(User).filter(User.role == UserRole.PANEL_LAWYER).first()
    assign_payload = {
        "lawyer_id": lawyer.id,
        "notes": "Assigned for partition suit preparation and court filing."
    }
    assign_res = client.post(f"/api/v1/cases/{case_id}/assign", json=assign_payload, headers=dlao_headers)
    assert assign_res.status_code == 200
    assigned_data = assign_res.json()
    assert assigned_data["status"] == CaseStatus.LAWYER_REVIEW
    assert assigned_data["assigned_lawyer_id"] == lawyer.id


@pytest.mark.asyncio
async def test_alternative_path_needs_information(db, client, dlao_headers):
    """
    Test alternative lifecycle path:
    PENDING_HUMAN_REVIEW -> NEEDS_INFORMATION -> VERIFIED
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    assert case is not None

    req_info_payload = {
        "info_needed": "Please upload a copy of the land mutation certificate and tax payment receipt."
    }
    res = client.post(f"/api/v1/cases/{case.id}/request-info", json=req_info_payload, headers=dlao_headers)
    assert res.status_code == 200
    assert res.json()["status"] == CaseStatus.NEEDS_INFORMATION

    # From NEEDS_INFORMATION, once applicant provides info, DLAO can verify
    verify_payload = {
        "notes": "Tax receipts received. Legal eligibility confirmed.",
        "route_to_panel_queue": True
    }
    verify_res = client.post(f"/api/v1/cases/{case.id}/verify", json=verify_payload, headers=dlao_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == CaseStatus.PANEL_LAWYER_QUEUE


@pytest.mark.asyncio
async def test_alternative_path_rejection(db, client, dlao_headers):
    """
    Test alternative lifecycle path:
    PENDING_HUMAN_REVIEW -> REJECTED
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    assert case is not None

    reject_payload = {
        "reason": "Applicant household income exceeds statutory ceiling under Legal Aid Act 2000."
    }
    res = client.post(f"/api/v1/cases/{case.id}/reject", json=reject_payload, headers=dlao_headers)
    assert res.status_code == 200
    assert res.json()["status"] == CaseStatus.REJECTED


@pytest.mark.asyncio
async def test_invalid_state_transitions(db, client, dlao_headers):
    """
    Assert that invalid direct jumps or illegal transitions fail with HTTP 400.
    """
    # Create NEW case
    new_case = Case(
        tracking_id="DLAS-TEST-9999",
        title="Test Invalid Jumps",
        description="Testing invalid transitions",
        applicant_name="Test Applicant",
        applicant_phone="+8801700000000",
        district="Dhaka",
        status=CaseStatus.NEW,
    )
    db.add(new_case)
    db.commit()

    # Attempting to assign lawyer directly to a NEW case (must be PANEL_LAWYER_QUEUE)
    lawyer = db.query(User).filter(User.role == UserRole.PANEL_LAWYER).first()
    assign_res = client.post(
        f"/api/v1/cases/{new_case.id}/assign",
        json={"lawyer_id": lawyer.id},
        headers=dlao_headers
    )
    assert assign_res.status_code == 400

    # Attempting to verify a NEW case (must be PENDING_HUMAN_REVIEW)
    verify_res = client.post(
        f"/api/v1/cases/{new_case.id}/verify",
        json={"notes": "premature verification"},
        headers=dlao_headers
    )
    assert verify_res.status_code == 400
