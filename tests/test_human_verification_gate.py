from app.models.case import Case, CaseStatus


def test_ai_role_blocked_from_verifying_case(client, ai_headers, db):
    """
    SECURITY INVARIANT:
    Automated AI (Gemini / system_ai) must NEVER directly verify a case.
    Must return 403 Forbidden.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    assert case is not None

    payload = {"notes": "AI auto-verification attempt", "route_to_panel_queue": True}
    res = client.post(f"/api/v1/cases/{case.id}/verify", json=payload, headers=ai_headers)
    assert res.status_code == 403
    assert "automated ai" in res.json()["detail"].lower() or "forbidden" in res.json()["detail"].lower()


def test_ai_role_blocked_from_assigning_lawyer(client, ai_headers, db):
    """
    SECURITY INVARIANT:
    Automated AI (Gemini / system_ai) must NEVER assign panel lawyers.
    Must return 403 Forbidden.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PANEL_LAWYER_QUEUE).first()
    assert case is not None

    payload = {"lawyer_id": 1}
    res = client.post(f"/api/v1/cases/{case.id}/assign", json=payload, headers=ai_headers)
    assert res.status_code == 403


def test_ai_role_blocked_from_rejecting_case(client, ai_headers, db):
    """
    SECURITY INVARIANT:
    Automated AI (Gemini / system_ai) must NEVER reject a case.
    Must return 403 Forbidden.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    assert case is not None

    payload = {"reason": "AI automated rejection"}
    res = client.post(f"/api/v1/cases/{case.id}/reject", json=payload, headers=ai_headers)
    assert res.status_code == 403


def test_ai_role_blocked_from_archiving_case(client, ai_headers, db):
    """
    SECURITY INVARIANT:
    Automated AI (Gemini / system_ai) must NEVER archive or delete a case.
    Must return 403 Forbidden.
    """
    case = db.query(Case).first()
    payload = {"authorization": True, "reason": "AI automated deletion"}
    res = client.post(f"/api/v1/cases/{case.id}/archive", json=payload, headers=ai_headers)
    assert res.status_code == 403


def test_unauthorized_roles_blocked_from_verification(client, applicant_headers, lawyer_headers, db):
    """
    Neither citizens (applicants) nor panel lawyers may verify cases.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    payload = {"notes": "Unauthorized verification"}

    # Applicant
    res_app = client.post(f"/api/v1/cases/{case.id}/verify", json=payload, headers=applicant_headers)
    assert res_app.status_code == 403

    # Panel Lawyer
    res_law = client.post(f"/api/v1/cases/{case.id}/verify", json=payload, headers=lawyer_headers)
    assert res_law.status_code == 403


def test_human_dlao_can_verify_case(client, dlao_headers, db):
    """
    Only authorized human DLAO officers can verify cases into PANEL_LAWYER_QUEUE.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    payload = {
        "notes": "Verified by human judicial officer. Financial distress criteria confirmed.",
        "route_to_panel_queue": True
    }
    res = client.post(f"/api/v1/cases/{case.id}/verify", json=payload, headers=dlao_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == CaseStatus.PANEL_LAWYER_QUEUE
    assert data["verified_by_id"] is not None
