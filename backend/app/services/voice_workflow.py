import datetime
import uuid
import logging
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.case import Case, CaseStatus, CasePriority, LegalCategory
from app.models.voice_intake import (
    VoiceCallSession,
    VoiceIntakeAnswer,
    VoiceIntakeStep,
    FIXED_QUESTIONS,
)
from app.models.audit import AuditLog, AuditAction
from app.services.case_workflow import generate_tracking_id
from app.services.gemini_voice import gemini_voice_service
from app.realtime import ws_hub
from app.utils import now_utc

logger = logging.getLogger("dlas.voice_workflow")

NEXT_STEP_MAP = {
    VoiceIntakeStep.CALL_STARTED: VoiceIntakeStep.RELAY_CONFIRM,
    VoiceIntakeStep.RELAY_CONFIRM: VoiceIntakeStep.Q0,
    VoiceIntakeStep.Q0: VoiceIntakeStep.Q1,
    VoiceIntakeStep.Q1: VoiceIntakeStep.Q2,
    VoiceIntakeStep.Q2: VoiceIntakeStep.Q3,
    VoiceIntakeStep.Q3: VoiceIntakeStep.COMPLETED,
}


class VoiceWorkflowManager:
    """
    Authoritative state machine and workflow controller for DLAS telephony & browser voice intake.
    Enforces sequence, per-answer immediate persistence, and danger/urgency assessment.
    """

    def start_session(
        self,
        session_id: Optional[str] = None,
        caller_phone: Optional[str] = None,
        is_browser_simulated: bool = False,
        applicant_name: Optional[str] = None,
        district: Optional[str] = "Dhaka",
        db: Session = None,
    ) -> Tuple[VoiceCallSession, Case]:
        if not session_id:
            session_id = f"sim_{uuid.uuid4().hex[:12]}"

        # Check existing session
        existing = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
        if existing and existing.case:
            return existing, existing.case

        caller_num = caller_phone or "+8801711000001"
        tracking_id = generate_tracking_id(db)

        # 1. Create linked Case in state AI_INTAKE
        case = Case(
            tracking_id=tracking_id,
            title=f"[Voice Helpline] Intake - {applicant_name or caller_num}",
            title_bn=f"[ভয়েস হেল্পলাইন] আবেদন - {applicant_name or caller_num}",
            description="Automated Bangla telephony intake call started. Awaiting question responses.",
            description_bn="স্বয়ংক্রিয় ভয়েস কল শুরু হয়েছে। প্রশ্নোত্তরের অপেক্ষায় রয়েছে।",
            status=CaseStatus.AI_INTAKE,
            priority=CasePriority.MEDIUM,
            legal_category=LegalCategory.CIVIL_GENERAL,
            applicant_name=applicant_name or "Voice Helpline Caller",
            applicant_phone=caller_num,
            district=district or "Dhaka",
            intake_channel="PHONE_VOICE" if not is_browser_simulated else "BROWSER_VOICE_SIMULATOR",
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        db.add(case)
        db.flush()

        # 2. Create VoiceCallSession
        session = VoiceCallSession(
            session_id=session_id,
            caller_phone=caller_num,
            current_step=VoiceIntakeStep.RELAY_CONFIRM,
            case_id=case.id,
            is_browser_simulated=is_browser_simulated,
            danger_detected=False,
            risk_flags=[],
            suggested_priority=CasePriority.MEDIUM,
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        db.refresh(case)

        # 3. Broadcast CASE_CREATED
        ws_hub.broadcast_event_sync(
            event_type="CASE_CREATED",
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "status": case.status,
                "priority": case.priority,
                "caller_phone": caller_num,
                "channel": case.intake_channel,
            },
            actor={"name": "Voice Intake Engine", "role": "system"},
        )

        return session, case

    def process_step_answer(
        self,
        session_id: str,
        question_id: str,
        spoken_answer: str,
        db: Session,
        source: str = "CALLER_SPOKEN",
        confidence: float = 1.0,
    ) -> Dict[str, Any]:
        session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
        if not session:
            raise ValueError(f"Voice session '{session_id}' not found.")

        case = db.query(Case).filter(Case.id == session.case_id).first()
        if not case:
            raise ValueError(f"Case associated with session '{session_id}' not found.")

        # Fixed Sequence Validation
        valid_question_for_step = {
            VoiceIntakeStep.CALL_STARTED: "RELAY_CONFIRM",
            VoiceIntakeStep.RELAY_CONFIRM: "Q0",
            VoiceIntakeStep.Q0: "Q0",
            VoiceIntakeStep.Q1: "Q1",
            VoiceIntakeStep.Q2: "Q2",
            VoiceIntakeStep.Q3: "Q3",
        }

        expected_q = valid_question_for_step.get(session.current_step, session.current_step)
        # Allow answering current step or expected question
        if question_id not in [expected_q, session.current_step]:
            logger.warning(f"Out of order answer received. Session step: {session.current_step}, submitted: {question_id}")

        # AI Voice analysis on spoken transcript
        analysis = gemini_voice_service.analyze_answer(question_id=question_id, answer_text=spoken_answer)
        question_meta = FIXED_QUESTIONS.get(question_id, {"bn": question_id, "en": question_id})

        # 1. Immediate per-answer persistence
        answer_record = VoiceIntakeAnswer(
            session_id=session.session_id,
            case_id=case.id,
            question_id=question_id,
            question=question_meta["bn"],
            answer=spoken_answer,
            source=source,
            confidence=confidence,
            danger_detected=analysis.get("danger_detected", False),
            danger_notes=analysis.get("danger_notes"),
            timestamp=now_utc(),
        )
        db.add(answer_record)

        # 2. Risk Evaluation & Updates
        if analysis.get("danger_detected"):
            session.danger_detected = True
            current_flags = list(session.risk_flags or [])
            for f in analysis.get("risk_flags", []):
                if f not in current_flags:
                    current_flags.append(f)
            session.risk_flags = current_flags
            session.suggested_priority = CasePriority.EMERGENCY

        if question_id == "Q0":
            consent_val = analysis.get("consent_given", True)
            session.consent_given = consent_val
            if consent_val is False:
                session.current_step = VoiceIntakeStep.ABORTED

        if question_id == "Q1":
            cat = analysis.get("extracted_entities", {}).get("legal_category")
            if cat:
                case.legal_category = cat
            app_name = analysis.get("extracted_entities", {}).get("applicant_name")
            if app_name:
                case.applicant_name = app_name

        if question_id == "Q3":
            safe_time = analysis.get("extracted_entities", {}).get("safe_contact_time")
            if safe_time:
                session.safe_contact_time = safe_time

        # 3. Advance to Next Step in Sequence
        next_step = NEXT_STEP_MAP.get(question_id, VoiceIntakeStep.COMPLETED)
        if session.current_step != VoiceIntakeStep.ABORTED:
            session.current_step = next_step

        session.updated_at = now_utc()
        case.updated_at = now_utc()
        db.commit()
        db.refresh(session)
        db.refresh(case)
        db.refresh(answer_record)

        # 4. Immediate Realtime Broadcast of CASE_UPDATED
        ws_hub.broadcast_event_sync(
            event_type="CASE_UPDATED",
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "status": case.status,
                "session_id": session.session_id,
                "completed_question": question_id,
                "next_step": session.current_step,
                "danger_detected": session.danger_detected,
                "risk_flags": session.risk_flags,
            },
            actor={"name": "Voice Intake Engine", "role": "system"},
        )

        # 5. Check if call sequence is completed
        is_completed = (session.current_step == VoiceIntakeStep.COMPLETED)
        if is_completed:
            final_summary = self.finalize_session(session.session_id, db)
            return {
                "session": session,
                "case": case,
                "answer": answer_record,
                "next_step": session.current_step,
                "is_call_completed": True,
                "final_summary": final_summary,
            }

        next_prompt = FIXED_QUESTIONS.get(session.current_step, {})
        return {
            "session": session,
            "case": case,
            "answer": answer_record,
            "next_step": session.current_step,
            "next_prompt_text_bn": next_prompt.get("bn"),
            "next_prompt_text_en": next_prompt.get("en"),
            "is_call_completed": False,
        }

    def finalize_session(self, session_id: str, db: Session) -> Dict[str, Any]:
        session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
        if not session:
            raise ValueError(f"Voice session '{session_id}' not found.")

        case = db.query(Case).filter(Case.id == session.case_id).first()
        if not case:
            raise ValueError(f"Case associated with session '{session_id}' not found.")

        answers = db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session.session_id).order_by(VoiceIntakeAnswer.id).all()

        # Aggregate narrative from all answered questions
        transcript_lines = []
        for ans in answers:
            transcript_lines.append(f"[{ans.question_id}] {ans.question}\n-> {ans.answer}")

        full_narrative = "\n\n".join(transcript_lines)
        case.description = full_narrative

        # Danger & Urgency Rules
        if session.danger_detected or any(flag in (session.risk_flags or []) for flag in ["IMMEDIATE_DANGER", "CURRENT_VIOLENCE_OR_THREAT", "ABUSER_PRESENT", "CHILD_AT_RISK"]):
            case.priority = CasePriority.EMERGENCY
            case.ai_urgency_score = "URGENT_REVIEW"
            status_note = "EMERGENCY: Immediate danger, physical threat, or child vulnerability detected during voice intake."
        else:
            case.priority = CasePriority.MEDIUM
            case.ai_urgency_score = "NORMAL"
            status_note = "Standard voice intake completed. Awaiting DLAO review."

        # Case Status Transition: AI_INTAKE -> PENDING_HUMAN_REVIEW
        case.status = CaseStatus.PENDING_HUMAN_REVIEW
        case.ai_summary = f"Flags: {', '.join(session.risk_flags) if session.risk_flags else 'None'}. Safe Callback: {session.safe_contact_time or 'Standard'}. Note: {status_note}"
        case.updated_at = now_utc()
        session.current_step = VoiceIntakeStep.COMPLETED
        session.updated_at = now_utc()

        # Audit Log Event
        audit = AuditLog(
            case_id=case.id,
            actor_id=None,
            actor_name="Voice Intake System",
            actor_role="system",
            action=AuditAction.CASE_UPDATED,
            previous_state=CaseStatus.AI_INTAKE,
            new_state=case.status,
            notes=f"VOICE_INTAKE_COMPLETED: {len(answers)} questions answered. Flags: {', '.join(session.risk_flags) if session.risk_flags else 'None'}. Priority: {case.priority}.",
            timestamp=now_utc(),
        )
        db.add(audit)
        db.commit()
        db.refresh(case)
        db.refresh(session)

        # Broadcast final CASE_UPDATED
        ws_hub.broadcast_event_sync(
            event_type="CASE_UPDATED",
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "status": case.status,
                "priority": case.priority,
                "danger_detected": session.danger_detected,
                "risk_flags": session.risk_flags,
                "completed": True,
            },
            actor={"name": "Voice Intake Engine", "role": "system"},
        )

        return {
            "case_id": case.id,
            "tracking_id": case.tracking_id,
            "status": case.status,
            "priority": case.priority,
            "danger_detected": session.danger_detected,
            "risk_flags": session.risk_flags,
            "total_answers": len(answers),
        }


voice_workflow_manager = VoiceWorkflowManager()
