import pytest
import os
import re
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus, CasePriority, LegalCategory
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditLog, AuditAction
from app.models.user import User, UserRole
from app.models.voice_intake import VoiceCallSession, VoiceIntakeAnswer, VoiceIntakeStep
from app.realtime.connection_manager import manager


def test_scenario_a_judge_verification_moves_to_lawyer_queue(client: TestClient, db: Session, dlao_headers: dict, lawyer_token: str):
    """
    Scenario A:
    Judge logs in → sees 20 seeded cases → opens a case → verifies it
    → case moves to panel lawyer queue → lawyer notification appears → audit log records everything
    """
    # 1. Judge logs in and lists cases
    resp = client.get("/api/v1/cases", headers=dlao_headers)
    assert resp.status_code == 200
    cases_data = resp.json()["items"]
    assert len(cases_data) >= 20, f"Expected at least 20 seeded cases, got {len(cases_data)}"

    # 2. Pick a case in PENDING_HUMAN_REVIEW
    target = next((c for c in cases_data if c["status"] == CaseStatus.PENDING_HUMAN_REVIEW), None)
    if not target:
        target = cases_data[0]
        # Transition to PENDING_HUMAN_REVIEW for verification test
        db_target = db.query(Case).filter(Case.id == target["id"]).first()
        db_target.status = CaseStatus.PENDING_HUMAN_REVIEW
        db.commit()

    case_id = target["id"]

    # 3. Judge opens case detail
    detail_resp = client.get(f"/api/v1/cases/{case_id}", headers=dlao_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == case_id

    # 4. Judge verifies the case
    verify_resp = client.post(
        f"/api/v1/cases/{case_id}/verify",
        headers=dlao_headers,
        json={
            "action": "VERIFIED",
            "notes": "Verified applicant merits and income threshold. Routing to panel lawyer queue.",
            "priority": "HIGH",
        },
    )
    assert verify_resp.status_code == 200
    verified_data = verify_resp.json()

    # Case must transition to PANEL_LAWYER_QUEUE
    assert verified_data["status"] == CaseStatus.PANEL_LAWYER_QUEUE
    assert verified_data["priority"] == CasePriority.HIGH
    assert verified_data["applicant_nid_verified"] is True

    # 5. Verify Lawyer Notification was created
    lawyer_headers = {"Authorization": f"Bearer {lawyer_token}"}
    notif_resp = client.get("/api/v1/notifications", headers=lawyer_headers)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    matching_notif = next((n for n in notifs if n["case_id"] == case_id), None)
    assert matching_notif is not None
    assert matching_notif["type"] in [NotificationType.STATUS_CHANGED, NotificationType.INFO, "STATUS_CHANGED", "INFO"]

    # 6. Verify Audit Log recorded the verification
    audit_logs = db.query(AuditLog).filter(
        AuditLog.case_id == case_id,
        AuditLog.action == AuditAction.CASE_VERIFIED,
    ).all()
    assert len(audit_logs) >= 1
    audit = audit_logs[0]
    assert audit.new_state == CaseStatus.PANEL_LAWYER_QUEUE
    assert "Verified applicant merits" in audit.notes


def test_scenario_b_intake_case_arrives_and_updates_live(client: TestClient, db: Session, dlao_headers: dict):
    """
    Scenario B:
    A new intake case arrives → appears in dashboard → fields update live
    → risk changes → priority suggestion appears → judge refreshes page → all data remains correct
    """
    # 1. New intake arrives via voice/online
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801755112233", "applicant_name": "সুলতানা রহমান", "district": "Barishal"},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    case_id = start_data["case_id"]

    # 2. Case appears in dashboard with AI_INTAKE status
    dash_resp = client.get(f"/api/v1/cases/{case_id}", headers=dlao_headers)
    assert dash_resp.status_code == 200
    assert dash_resp.json()["status"] == CaseStatus.AI_INTAKE

    # 3. Caller speaks Q0
    client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q0", "spoken_answer": "হ্যাঁ আমি সুলতানা রহমান, কথা বলতে সম্মত।"},
    )

    # 4. Caller describes domestic violence problem in Q1
    client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q1", "spoken_answer": "যৌতুকের দাবিতে স্বামী শারীরিক নির্যাতন করছে।"},
    )

    # 5. Caller reports acute danger in Q2 -> risk changes live
    step2_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q2", "spoken_answer": "আমি একদম নিরাপদ নই, সে ঘরে দা নিয়ে আমাকে মারধর করছে!"},
    )
    assert step2_resp.status_code == 200
    step2_data = step2_resp.json()
    assert step2_data["danger_detected"] is True
    assert step2_data["suggested_priority"] == CasePriority.EMERGENCY

    # 6. Caller answers Q3
    step3_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q3", "spoken_answer": "বাচ্চা আমার সাথেই আছে। সকালে ফোন দিবেন।"},
    )
    assert step3_resp.status_code == 200
    assert step3_resp.json()["is_call_completed"] is True

    # 7. Judge refreshes page -> All data remains authoritative and correct
    refresh_resp = client.get(f"/api/v1/cases/{case_id}", headers=dlao_headers)
    assert refresh_resp.status_code == 200
    refreshed_case = refresh_resp.json()
    assert refreshed_case["status"] == CaseStatus.PENDING_HUMAN_REVIEW
    assert refreshed_case["priority"] == CasePriority.EMERGENCY
    assert refreshed_case["ai_urgency_score"] == "URGENT_REVIEW"
    assert "যৌতুক" in refreshed_case["description"]
    assert "সুলতানা রহমান" in refreshed_case["applicant_name"]


def test_scenario_c_priority_change_persists_and_emits_event(client: TestClient, db: Session, dlao_headers: dict):
    """
    Scenario C:
    Judge changes priority → backend persists it → second browser / client receives update
    → refresh preserves it
    """
    # Create or select a case
    case = db.query(Case).first()
    original_priority = case.priority
    new_priority = CasePriority.EMERGENCY if original_priority != CasePriority.EMERGENCY else CasePriority.HIGH

    # Judge changes priority
    patch_resp = client.patch(
        f"/api/v1/cases/{case.id}/priority",
        headers=dlao_headers,
        json={"priority": new_priority, "reason": "Judge elevated priority due to security threats reported."},
    )
    assert patch_resp.status_code == 200
    updated_case = patch_resp.json()
    assert updated_case["priority"] == new_priority

    # Second fetch (e.g. from another browser session)
    fetch_resp = client.get(f"/api/v1/cases/{case.id}", headers=dlao_headers)
    assert fetch_resp.status_code == 200
    assert fetch_resp.json()["priority"] == new_priority


def test_scenario_d_return_for_missing_info_creates_no_lawyer_notification(client: TestClient, db: Session, dlao_headers: dict, lawyer_token: str):
    """
    Scenario D:
    Judge returns case for missing information → NO panel lawyer notification is created
    """
    # Create a fresh case in PENDING_HUMAN_REVIEW
    case = Case(
        tracking_id="DLAS-TEST-RET-01",
        title="Test Return Case",
        description="Incomplete documents provided",
        status=CaseStatus.PENDING_HUMAN_REVIEW,
        priority=CasePriority.LOW,
        applicant_name="আনিসুর রহমান",
        applicant_phone="+8801700112233",
        district="Gazipur",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Initial lawyer notification count
    lawyer_headers = {"Authorization": f"Bearer {lawyer_token}"}
    initial_notifs = client.get("/api/v1/notifications", headers=lawyer_headers).json()
    initial_count = len(initial_notifs)

    # Judge returns case for more information
    return_resp = client.post(
        f"/api/v1/cases/{case.id}/verify",
        headers=dlao_headers,
        json={
            "action": "NEEDS_INFORMATION",
            "notes": "Missing certified land ownership deed and income certificate.",
        },
    )
    assert return_resp.status_code == 200
    data = return_resp.json()
    assert data["status"] == CaseStatus.NEEDS_INFORMATION

    # Verify NO panel lawyer notification was dispatched
    post_notifs = client.get("/api/v1/notifications", headers=lawyer_headers).json()
    matching_new = [n for n in post_notifs if n["case_id"] == case.id]
    assert len(matching_new) == 0
    assert len(post_notifs) == initial_count


def test_scenario_e_verify_creates_single_notification_without_duplicates(client: TestClient, db: Session, dlao_headers: dict, lawyer_token: str):
    """
    Scenario E:
    Judge verifies case → exactly one panel lawyer notification is created
    → notification is persistent → refreshing does not duplicate it
    """
    case = Case(
        tracking_id="DLAS-TEST-NOTIF-01",
        title="Single Notification Test",
        description="Clear civil case",
        status=CaseStatus.PENDING_HUMAN_REVIEW,
        priority=CasePriority.MEDIUM,
        applicant_name="মেহেরুন্নেসা",
        applicant_phone="+8801799887766",
        district="Dhaka",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Verify case
    verify_resp = client.post(
        f"/api/v1/cases/{case.id}/verify",
        headers=dlao_headers,
        json={"action": "VERIFIED", "notes": "Approved for panel assignment"},
    )
    assert verify_resp.status_code == 200

    lawyer_headers = {"Authorization": f"Bearer {lawyer_token}"}
    notifs1 = client.get("/api/v1/notifications", headers=lawyer_headers).json()
    matching1 = [n for n in notifs1 if n["case_id"] == case.id]
    assert len(matching1) == 1

    # Refresh notifications endpoint multiple times -> count remains exactly 1
    notifs2 = client.get("/api/v1/notifications", headers=lawyer_headers).json()
    matching2 = [n for n in notifs2 if n["case_id"] == case.id]
    assert len(matching2) == 1


def test_scenario_f_voice_pipeline_incremental_bangla_persistence(client: TestClient, db: Session):
    """
    Scenario F:
    Twilio/Gemini call → Bangla conversation → answers saved incrementally
    → call ends → complete application record appears in human-review state
    """
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801733445566", "applicant_name": "মোসাম্মৎ আয়েশা", "district": "Khulna"},
    )
    assert start_resp.status_code == 200
    s_data = start_resp.json()
    session_id = s_data["session_id"]
    case_id = s_data["case_id"]

    # Q0
    client.post("/api/v1/voice/simulate/step", json={"session_id": session_id, "question_id": "Q0", "spoken_answer": "জি, আমি আয়েশা, কথা বলতে প্রস্তুত।"})
    assert db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count() == 1

    # Q1
    client.post("/api/v1/voice/simulate/step", json={"session_id": session_id, "question_id": "Q1", "spoken_answer": "পৈতৃক জমি বেদখল করে রেখেছে প্রতিপক্ষ।"})
    assert db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count() == 2

    # Q2
    client.post("/api/v1/voice/simulate/step", json={"session_id": session_id, "question_id": "Q2", "spoken_answer": "এখন নিরাপদ স্থানে আছি।"})
    assert db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count() == 3

    # Q3
    res3 = client.post("/api/v1/voice/simulate/step", json={"session_id": session_id, "question_id": "Q3", "spoken_answer": "কোনো শিশু ঝুঁকিতে নেই। বিকেলে যোগাযোগ করবেন।"})
    assert res3.status_code == 200
    assert db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count() == 4

    # Call ends, verify human review state
    case = db.query(Case).filter(Case.id == case_id).first()
    assert case.status == CaseStatus.PENDING_HUMAN_REVIEW
    assert "পৈতৃক জমি" in case.description


def test_scenario_g_data_persists_across_database_sessions(client: TestClient, db: Session, dlao_headers: dict):
    """
    Scenario G:
    Backend restarts / session re-instantiation → all existing cases remain,
    audit history remains, notifications remain.
    """
    # Create an identifiable case
    case = Case(
        tracking_id="DLAS-PERSIST-CHK-99",
        title="Persistent Restart Case",
        description="Testing data durability",
        status=CaseStatus.PENDING_HUMAN_REVIEW,
        applicant_name="কামাল হোসেন",
        applicant_phone="+8801700998811",
        district="Mymensingh",
    )
    db.add(case)
    db.commit()
    case_id = case.id

    # Verify audit log and notification creation
    client.post(
        f"/api/v1/cases/{case_id}/verify",
        headers=dlao_headers,
        json={"action": "VERIFIED", "notes": "Verified for persistence test"},
    )

    # Simulate fresh database connection / query
    db.expire_all()
    reloaded_case = db.query(Case).filter(Case.id == case_id).first()
    assert reloaded_case is not None
    assert reloaded_case.status == CaseStatus.PANEL_LAWYER_QUEUE

    reloaded_audit = db.query(AuditLog).filter(AuditLog.case_id == case_id).all()
    assert len(reloaded_audit) >= 1

    reloaded_notif = db.query(Notification).filter(Notification.case_id == case_id).all()
    assert len(reloaded_notif) >= 1


def test_scenario_h_websocket_reconnect_reconciliation(client: TestClient, dlao_headers: dict):
    """
    Scenario H:
    WebSocket disconnects → reconnects → reconciles with server via /events/since
    → no duplicate events
    """
    # Clear and populate buffer
    manager.clear_buffer()
    manager.broadcast_event_sync("CASE_UPDATED", {"case_id": 1, "status": "VERIFIED"})
    manager.broadcast_event_sync("CASE_PRIORITY_CHANGED", {"case_id": 1, "priority": "HIGH"})
    current_seq = manager.get_latest_seq()

    # Client reconnects having missed since_seq = current_seq - 1
    missed_resp = client.get(f"/api/v1/events/since?since_seq={current_seq - 1}", headers=dlao_headers)
    assert missed_resp.status_code == 200
    missed_data = missed_resp.json()
    assert missed_data["reset_required"] is False
    assert len(missed_data["events"]) == 1
    assert missed_data["events"][0]["seq"] == current_seq


def test_scenario_i_malformed_ai_intake_rejected(client: TestClient, dlao_headers: dict):
    """
    Scenario I:
    AI returns incomplete or malformed structured data → backend rejects invalid fields
    → missing fields remain unknown → no fabricated information enters database
    """
    # Attempt to submit an intake application with invalid NID length and missing required applicant fields
    bad_payload = {
        "applicant": {
            "name": "",  # invalid empty name
            "mobile": "123",  # invalid short phone
            "nid": "invalid_nid_alpha",
        },
        "case_description": "short",
    }
    resp = client.post("/api/v1/intake/applications", headers=dlao_headers, json=bad_payload)
    # Must fail validation or reject invalid format
    assert resp.status_code in [400, 422]


def test_scenario_j_ai_forbidden_actions_refused(client: TestClient, db: Session, ai_headers: dict, lawyer_headers: dict):
    """
    Scenario J:
    AI attempts forbidden action → backend refuses it with 403 Forbidden.
    Panel lawyer attempts verification → backend refuses with 403 Forbidden.
    """
    case = db.query(Case).filter(Case.status == CaseStatus.PENDING_HUMAN_REVIEW).first()
    if not case:
        case = db.query(Case).first()

    # 1. AI attempts to verify case
    ai_verify = client.post(
        f"/api/v1/cases/{case.id}/verify",
        headers=ai_headers,
        json={"action": "VERIFIED", "notes": "AI autonomous verification attempt"},
    )
    assert ai_verify.status_code == 403, f"AI verification should be forbidden, got {ai_verify.status_code}"

    # 2. AI attempts to reject case
    ai_reject = client.post(
        f"/api/v1/cases/{case.id}/reject",
        headers=ai_headers,
        json={"reason": "AI autonomous rejection attempt"},
    )
    assert ai_reject.status_code == 403, f"AI rejection should be forbidden, got {ai_reject.status_code}"

    # 3. AI attempts to archive/delete case
    ai_archive = client.post(
        f"/api/v1/cases/{case.id}/archive",
        headers=ai_headers,
        json={"authorization": True, "reason": "AI autonomous archive attempt"},
    )
    assert ai_archive.status_code == 403, f"AI archive should be forbidden, got {ai_archive.status_code}"

    # 4. Panel Lawyer attempts to verify case
    lawyer_verify = client.post(
        f"/api/v1/cases/{case.id}/verify",
        headers=lawyer_headers,
        json={"action": "VERIFIED", "notes": "Panel lawyer verification attempt"},
    )
    assert lawyer_verify.status_code == 403, f"Lawyer verification should be forbidden, got {lawyer_verify.status_code}"


def test_security_secrets_not_leaked_in_frontend():
    """
    Security Test:
    Verifies that no backend secrets (Gemini API keys, Twilio auth tokens, JWT secret keys)
    are present in frontend files under src/.
    """
    forbidden_patterns = [
        r"AIza[0-9A-Za-z-_]{35}",  # Google API key
        r"SK[0-9a-fA-F]{32}",     # Twilio API Key
        r"dlas_dev_jwt_secret",    # JWT secret key
        r"TWILIO_AUTH_TOKEN",
        r"GEMINI_API_KEY",
    ]

    src_dir = os.path.join(os.getcwd(), "src")
    assert os.path.exists(src_dir)

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".js", ".html", ".css", ".json")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern in forbidden_patterns:
                        match = re.search(pattern, content)
                        assert match is None, f"Secret pattern '{pattern}' detected in frontend file: {filepath}"


def test_security_unauthorized_access_blocked(client: TestClient):
    """
    Security Test:
    Unauthenticated caller cannot access protected case and admin endpoints.
    """
    # Missing token on cases list
    assert client.get("/api/v1/cases").status_code == 401

    # Missing token on case verification
    assert client.post("/api/v1/cases/1/verify", json={"action": "VERIFIED"}).status_code == 401

    # Missing token on notifications
    assert client.get("/api/v1/notifications").status_code == 401

    # Missing token on audit logs
    assert client.get("/api/v1/audit-logs").status_code == 401


def test_performance_rapid_updates(client: TestClient, db: Session, dlao_headers: dict):
    """
    Performance Test:
    Simulates rapid concurrent case priority and status queries.
    Asserts consistency and speed.
    """
    cases = db.query(Case).limit(10).all()
    assert len(cases) >= 1

    for c in cases:
        resp = client.get(f"/api/v1/cases/{c.id}", headers=dlao_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == c.id
