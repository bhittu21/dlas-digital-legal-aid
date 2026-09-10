import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus, CasePriority, LegalCategory
from app.models.voice_intake import VoiceCallSession, VoiceIntakeAnswer, VoiceIntakeStep
from app.models.audit import AuditLog


def test_voice_simulate_session_creation(client: TestClient, db: Session):
    """
    Verifies that initiating simulated voice intake creates a session,
    registers the case in AI_INTAKE status, and returns the statutory Bangla greeting.
    """
    response = client.post(
        "/api/v1/voice/simulate/start",
        json={
            "caller_phone": "+8801812345678",
            "applicant_name": "রাবেয়া খাতুন",
            "district": "Rangpur",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "session_id" in data
    assert data["session_id"].startswith("sim_")
    assert "case_id" in data
    assert data["tracking_id"].startswith("DLAS-")
    assert data["current_step"] == "RELAY_CONFIRM"
    assert data["prompt_id"] == "Q0"
    assert "জাতীয় আইনগত সহায়তা হেল্পলাইনে স্বাগতম" in data["prompt_text_bn"]
    assert "কথা বলতে সম্মত" in data["prompt_text_bn"]

    # Verify DB state
    session_id = data["session_id"]
    case_id = data["case_id"]

    db_session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
    assert db_session is not None
    assert db_session.caller_phone == "+8801812345678"
    assert db_session.is_browser_simulated is True

    db_case = db.query(Case).filter(Case.id == case_id).first()
    assert db_case is not None
    assert db_case.status == CaseStatus.AI_INTAKE
    assert db_case.applicant_name == "রাবেয়া খাতুন"
    assert db_case.district == "Rangpur"


def test_voice_intake_sequential_answers_and_immediate_persistence(client: TestClient, db: Session):
    """
    CRITICAL REQUIREMENT:
    Store each answer immediately after receiving it. Do NOT wait until call ends.
    Every answer must contain: question_id, question, answer, source, timestamp, confidence, case_id.
    """
    # 1. Start Session
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801711223344", "applicant_name": "নাসরিন আক্তার", "district": "Sylhet"},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    case_id = start_data["case_id"]

    # 2. Answer Q0 (Consent)
    step0_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q0",
            "spoken_answer": "হ্যাঁ, আমি নাসরিন আক্তার এবং আমি কথা বলতে সম্মত।",
            "source": "BROWSER_SIMULATED",
            "confidence": 0.98,
        },
    )
    assert step0_resp.status_code == 200
    data0 = step0_resp.json()
    assert data0["completed_question_id"] == "Q0"
    assert data0["next_step"] == "Q1"
    assert data0["is_call_completed"] is False

    # IMMEDIATELY inspect database to verify answer is stored BEFORE subsequent steps
    ans0 = db.query(VoiceIntakeAnswer).filter(
        VoiceIntakeAnswer.session_id == session_id,
        VoiceIntakeAnswer.question_id == "Q0",
    ).first()
    assert ans0 is not None
    assert ans0.question_id == "Q0"
    assert "কথা বলতে সম্মত" in ans0.question
    assert ans0.answer == "হ্যাঁ, আমি নাসরিন আক্তার এবং আমি কথা বলতে সম্মত।"
    assert ans0.source == "BROWSER_SIMULATED"
    assert ans0.confidence == 0.98
    assert ans0.case_id == case_id
    assert ans0.timestamp is not None

    # 3. Answer Q1 (Grievance Narrative)
    step1_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q1",
            "spoken_answer": "আমার স্বামী আমার দেনমোহর এবং খোরপোশ না দিয়ে ডিভোর্স দিয়েছে।",
            "source": "BROWSER_SIMULATED",
            "confidence": 0.95,
        },
    )
    assert step1_resp.status_code == 200
    data1 = step1_resp.json()
    assert data1["completed_question_id"] == "Q1"
    assert data1["next_step"] == "Q2"

    # Immediately check DB has 2 persisted answers
    ans_count = db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count()
    assert ans_count == 2

    # Check that legal category was extracted from narrative
    db_case = db.query(Case).filter(Case.id == case_id).first()
    assert db_case.legal_category == LegalCategory.FAMILY_MATRIMONIAL

    # 4. Answer Q2 (Immediate Safety)
    step2_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q2",
            "spoken_answer": "আমি এখন বাবার বাড়িতে আছি, নিরাপদে আছি। সে কাছে নেই।",
            "source": "BROWSER_SIMULATED",
            "confidence": 0.96,
        },
    )
    assert step2_resp.status_code == 200
    data2 = step2_resp.json()
    assert data2["completed_question_id"] == "Q2"
    assert data2["next_step"] == "Q3"
    assert data2["danger_detected"] is False

    ans_count = db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).count()
    assert ans_count == 3

    # 5. Answer Q3 (Child Risk & Callback protocol)
    step3_resp = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q3",
            "spoken_answer": "আমার সাথে আমার সন্তান আছে, নিরাপদে আছে। আমাকে সকালে বা বিকেলে ফোন দিলে ভালো হয়।",
            "source": "BROWSER_SIMULATED",
            "confidence": 0.97,
        },
    )
    assert step3_resp.status_code == 200
    data3 = step3_resp.json()
    assert data3["completed_question_id"] == "Q3"
    assert data3["is_call_completed"] is True
    assert data3["case_status"] == CaseStatus.PENDING_HUMAN_REVIEW

    # Total 4 answers persisted immediately
    all_answers = db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session_id).order_by(VoiceIntakeAnswer.id).all()
    assert len(all_answers) == 4
    for ans in all_answers:
        assert ans.case_id == case_id
        assert ans.question_id in ["Q0", "Q1", "Q2", "Q3"]
        assert ans.answer is not None
        assert ans.timestamp is not None
        assert ans.source == "BROWSER_SIMULATED"
        assert ans.confidence > 0

    # Verify Final Case State
    db.refresh(db_case)
    assert db_case.status == CaseStatus.PENDING_HUMAN_REVIEW
    assert db_case.priority == CasePriority.MEDIUM
    assert "দেনমোহর" in db_case.description
    assert "সকালে" in db_case.ai_summary or "Morning" in db_case.ai_summary

    # Verify Audit Log
    audit = db.query(AuditLog).filter(
        AuditLog.case_id == case_id,
        AuditLog.actor_name == "Voice Intake System",
    ).first()
    assert audit is not None
    assert "VOICE_INTAKE_COMPLETED" in audit.notes
    assert "4 questions answered" in audit.notes


def test_voice_intake_danger_detection_and_urgent_review(client: TestClient, db: Session):
    """
    Verifies that detection of immediate danger, violence, threats, or abuser proximity:
    - Flags danger_detected = True
    - Triggers URGENT_REVIEW / EMERGENCY priority
    - Transitions to PENDING_HUMAN_REVIEW with critical escalation flags
    """
    # Start session
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801999888777", "district": "Chattogram"},
    )
    session_id = start_resp.json()["session_id"]
    case_id = start_resp.json()["case_id"]

    # Q0: Consent
    client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q0", "spoken_answer": "হ্যাঁ আমি বলতে চাই।"},
    )

    # Q1: Physical abuse narrative
    client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q1",
            "spoken_answer": "যৌতুকের জন্য আমার স্বামী আমাকে পিটিয়েছে এবং নির্যাতন করছে।",
        },
    )

    # Q2: Acute danger & Abuser present
    step2 = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q2",
            "spoken_answer": "আমি একদম নিরাপদ নই, ভয়ে আছি! সে এখন দা নিয়ে আমার সামনে ঘরে আছে এবং মেরে ফেলার হুমকি দিচ্ছে!",
        },
    )
    assert step2.status_code == 200
    d2 = step2.json()
    assert d2["danger_detected"] is True
    assert "CURRENT_VIOLENCE_OR_THREAT" in d2["risk_flags"]
    assert "ABUSER_PRESENT" in d2["risk_flags"]
    assert "IMMEDIATE_DANGER" in d2["risk_flags"]
    assert d2["suggested_priority"] == CasePriority.EMERGENCY

    # Q3: Child at risk
    step3 = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q3",
            "spoken_answer": "আমার ছোট বাচ্চা বিপদে আছে, বাচ্চাকেও মারধর করতে চায়। ভবিষ্যতে শুধু দুপুরে যোগাযোগ করবেন।",
        },
    )
    assert step3.status_code == 200
    d3 = step3.json()
    assert d3["danger_detected"] is True
    assert "CHILD_AT_RISK" in d3["risk_flags"]
    assert d3["is_call_completed"] is True

    # Authoritative DB verification
    db_case = db.query(Case).filter(Case.id == case_id).first()
    assert db_case.priority == CasePriority.EMERGENCY
    assert db_case.ai_urgency_score == "URGENT_REVIEW"
    assert db_case.status == CaseStatus.PENDING_HUMAN_REVIEW
    assert "EMERGENCY" in db_case.ai_summary
    assert "CHILD_AT_RISK" in db_case.ai_summary


def test_voice_intake_refusal_abort(client: TestClient, db: Session):
    """
    Verifies that explicit refusal of consent at Q0 transitions the session to ABORTED.
    """
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801555444333"},
    )
    session_id = start_resp.json()["session_id"]

    step0 = client.post(
        "/api/v1/voice/simulate/step",
        json={
            "session_id": session_id,
            "question_id": "Q0",
            "spoken_answer": "না, আমি কোনো কথা বলব না, এটা ভুল নম্বর।",
        },
    )
    assert step0.status_code == 200
    d0 = step0.json()
    assert d0["next_step"] == VoiceIntakeStep.ABORTED

    db_session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
    assert db_session.consent_given is False
    assert db_session.current_step == VoiceIntakeStep.ABORTED


def test_voice_session_detail_endpoint(client: TestClient, db: Session):
    """
    Verifies GET /simulate/session/{session_id} returns all answers and metadata.
    """
    start_resp = client.post(
        "/api/v1/voice/simulate/start",
        json={"caller_phone": "+8801666777888", "applicant_name": "ফাতিমা বেগম"},
    )
    session_id = start_resp.json()["session_id"]

    client.post(
        "/api/v1/voice/simulate/step",
        json={"session_id": session_id, "question_id": "Q0", "spoken_answer": "হ্যাঁ আমি ফাতিমা বেগম, কথা বলতে সম্মত।"},
    )

    detail_resp = client.get(f"/api/v1/voice/simulate/session/{session_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["session_id"] == session_id
    assert detail["caller_phone"] == "+8801666777888"
    assert len(detail["answers"]) == 1
    assert detail["answers"][0]["question_id"] == "Q0"


def test_twilio_incoming_webhook_twiml(client: TestClient, db: Session):
    """
    Verifies Twilio inbound call webhook generates valid Bangla TwiML and starts intake session.
    """
    response = client.post(
        "/api/v1/voice/twilio/incoming",
        data={
            "CallSid": "CA1234567890abcdef1234567890abcdef",
            "From": "+8801700998877",
            "To": "+12025550199",
        },
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    xml_content = response.text
    assert "<Response>" in xml_content
    assert '<Say language="bn-BD">' in xml_content
    assert '<Gather input="speech"' in xml_content
    assert "জাতীয় আইনগত সহায়তা হেল্পলাইনে স্বাগতম" in xml_content
    assert "CA1234567890abcdef1234567890abcdef" in xml_content

    # Check session created in DB
    db_session = db.query(VoiceCallSession).filter(
        VoiceCallSession.session_id == "CA1234567890abcdef1234567890abcdef"
    ).first()
    assert db_session is not None
    assert db_session.caller_phone == "+8801700998877"
    assert db_session.is_browser_simulated is False


def test_twilio_step_speech_gather_callback(client: TestClient, db: Session):
    """
    Verifies Twilio speech gather callback parses caller voice speech,
    immediately persists answer, and responds with the next question TwiML.
    """
    # 1. Initialize inbound call
    client.post(
        "/api/v1/voice/twilio/incoming",
        data={"CallSid": "CA999888777666555444333222111000", "From": "+8801712345678"},
    )

    # 2. Twilio sends speech result for Q0
    step_resp = client.post(
        "/api/v1/voice/twilio/step?session_id=CA999888777666555444333222111000&question_id=Q0",
        data={
            "CallSid": "CA999888777666555444333222111000",
            "SpeechResult": "হ্যাঁ আমি আছি এবং কথা বলতে সম্মত।",
            "Confidence": "0.94",
        },
    )
    assert step_resp.status_code == 200
    xml_content = step_resp.text
    assert '<Say language="bn-BD">' in xml_content
    assert "আপনার সমস্যাটি সংক্ষেপে বলবেন?" in xml_content
    assert "question_id=Q1" in xml_content

    # 3. Check immediate persistence in DB with TWILIO_IVR_SPEECH source
    ans = db.query(VoiceIntakeAnswer).filter(
        VoiceIntakeAnswer.session_id == "CA999888777666555444333222111000",
        VoiceIntakeAnswer.question_id == "Q0",
    ).first()
    assert ans is not None
    assert ans.source == "TWILIO_IVR_SPEECH"
    assert ans.answer == "হ্যাঁ আমি আছি এবং কথা বলতে সম্মত।"
    assert ans.confidence == 0.94


def test_twilio_call_status_callback(client: TestClient, db: Session):
    """
    Verifies Twilio call status callback records call duration and safely finalizes session.
    """
    # Initialize
    client.post(
        "/api/v1/voice/twilio/incoming",
        data={"CallSid": "CAcallstatus12345", "From": "+8801711122233"},
    )

    # Disconnect status
    status_resp = client.post(
        "/api/v1/voice/twilio/status",
        data={
            "CallSid": "CAcallstatus12345",
            "CallStatus": "completed",
            "CallDuration": "42",
        },
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "received"

    db_session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == "CAcallstatus12345").first()
    assert db_session.duration_seconds == 42
