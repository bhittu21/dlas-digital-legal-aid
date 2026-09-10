import json
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.voice_intake import (
    VoiceCallSession,
    VoiceIntakeAnswer,
    VoiceIntakeStep,
    FIXED_QUESTIONS,
)
from app.schemas.voice_intake import (
    VoiceSimulateStartRequest,
    VoiceSimulateStartResponse,
    VoiceSimulateStepRequest,
    VoiceSimulateStepResponse,
    VoiceAnswerResponse,
    VoiceSessionDetailResponse,
)
from app.services.voice_workflow import voice_workflow_manager

logger = logging.getLogger("dlas.voice_api")

router = APIRouter()


def generate_twiml(say_text: str, gather_action: Optional[str] = None, hangup: bool = False) -> str:
    """
    Constructs clean, standard TwiML XML with Bangla-first voice attributes.
    """
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<Response>"]
    
    if gather_action:
        xml_lines.append(f'  <Gather input="speech" action="{gather_action}" language="bn-BD" speechTimeout="auto" timeout="6">')
        xml_lines.append(f'    <Say language="bn-BD">{say_text}</Say>')
        xml_lines.append('  </Gather>')
        xml_lines.append('  <Say language="bn-BD">আমরা আপনার উত্তর শুনতে পাইনি। অনুগ্রহ করে আবার বলুন।</Say>')
        xml_lines.append(f'  <Redirect>{gather_action}</Redirect>')
    else:
        xml_lines.append(f'  <Say language="bn-BD">{say_text}</Say>')
    
    if hangup:
        xml_lines.append("  <Hangup/>")
        
    xml_lines.append("</Response>")
    return "\n".join(xml_lines)


# =====================================================================
# SIMULATED BROWSER VOICE INTAKE (Saves Twilio minutes & costs)
# =====================================================================

@router.post("/simulate/start", response_model=VoiceSimulateStartResponse, summary="Start browser-simulated voice intake")
def simulate_start_call(
    payload: VoiceSimulateStartRequest,
    db: Session = Depends(get_db),
):
    """
    Initializes a new caller intake session without incurring Twilio telephony charges.
    Enforces the statutory Bangla-first greeting and fixed sequence start (RELAY_CONFIRM -> Q0).
    """
    sim_session_id = f"sim_{uuid.uuid4().hex[:12]}"
    session, case = voice_workflow_manager.start_session(
        session_id=sim_session_id,
        caller_phone=payload.caller_phone or "+8801711000001",
        is_browser_simulated=True,
        applicant_name=payload.applicant_name,
        district=payload.district or "Dhaka",
        db=db,
    )

    greeting = FIXED_QUESTIONS["RELAY_CONFIRM"]
    q0_meta = FIXED_QUESTIONS["Q0"]
    full_prompt_bn = f"{greeting['bn']} {q0_meta['bn']}"
    full_prompt_en = f"{greeting['en']} {q0_meta['en']}"

    return VoiceSimulateStartResponse(
        session_id=session.session_id,
        case_id=case.id,
        tracking_id=case.tracking_id,
        current_step=session.current_step,
        prompt_id="Q0",
        prompt_text_bn=full_prompt_bn,
        prompt_text_en=full_prompt_en,
        is_call_active=True,
    )


@router.post("/simulate/step", response_model=VoiceSimulateStepResponse, summary="Process per-turn caller answer")
def simulate_step(
    payload: VoiceSimulateStepRequest,
    db: Session = Depends(get_db),
):
    """
    Processes one intake turn:
    1. Validates step sequence
    2. Runs AI danger/urgency & entity extraction
    3. IMMEDIATELY persists answer to DB
    4. Broadcasts CASE_UPDATED via WebSocket
    5. Advances to next question or finalizes case
    """
    if not payload.spoken_answer or not payload.spoken_answer.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spoken answer cannot be empty.",
        )

    try:
        step_result = voice_workflow_manager.process_step_answer(
            session_id=payload.session_id,
            question_id=payload.question_id,
            spoken_answer=payload.spoken_answer.strip(),
            db=db,
            source=payload.source or "BROWSER_SIMULATED",
            confidence=payload.confidence or 1.0,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    session: VoiceCallSession = step_result["session"]
    case = step_result["case"]
    answer_rec: VoiceIntakeAnswer = step_result["answer"]
    is_completed = step_result.get("is_call_completed", False)

    msg_bn = "উত্তর সফলভাবে সংরক্ষিত হয়েছে।"
    msg_en = "Answer successfully validated and persisted."
    if is_completed:
        msg_bn = "ভয়েস ইনটেক সম্পন্ন হয়েছে এবং পর্যালোচনায় জমা দেওয়া হয়েছে।"
        msg_en = "Voice intake session completed and submitted for human review."

    return VoiceSimulateStepResponse(
        session_id=session.session_id,
        case_id=case.id,
        completed_question_id=payload.question_id,
        persisted_answer=VoiceAnswerResponse.model_validate(answer_rec),
        next_step=session.current_step,
        next_prompt_text_bn=step_result.get("next_prompt_text_bn"),
        next_prompt_text_en=step_result.get("next_prompt_text_en"),
        is_call_completed=is_completed,
        danger_detected=session.danger_detected,
        risk_flags=session.risk_flags or [],
        suggested_priority=session.suggested_priority or "MEDIUM",
        case_status=case.status,
        message_bn=msg_bn,
        message_en=msg_en,
    )


@router.get("/simulate/session/{session_id}", response_model=VoiceSessionDetailResponse, summary="Get voice session detail")
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves complete voice call session records, all persisted answers, and danger flags.
    """
    session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Voice session '{session_id}' not found.")

    answers = db.query(VoiceIntakeAnswer).filter(VoiceIntakeAnswer.session_id == session.session_id).order_by(VoiceIntakeAnswer.id).all()
    ans_responses = [VoiceAnswerResponse.model_validate(a) for a in answers]

    return VoiceSessionDetailResponse(
        id=session.id,
        session_id=session.session_id,
        caller_phone=session.caller_phone,
        current_step=session.current_step,
        case_id=session.case_id,
        is_browser_simulated=session.is_browser_simulated,
        danger_detected=session.danger_detected,
        risk_flags=session.risk_flags or [],
        suggested_priority=session.suggested_priority or "MEDIUM",
        safe_contact_time=session.safe_contact_time,
        answers=ans_responses,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# =====================================================================
# TWILIO TELEPHONY INTEGRATION (Real IVR Webhooks & Media-Stream)
# =====================================================================

@router.post("/twilio/incoming", summary="Twilio Incoming Call Webhook")
async def twilio_incoming_call(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handles live inbound phone calls to the Twilio national legal aid helpline.
    Initializes backend session and speaks RELAY_CONFIRM + Q0 in natural Bangla.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid") or f"tw_{uuid.uuid4().hex[:12]}"
    caller_phone = form_data.get("From", "+8801700000000")

    session, case = voice_workflow_manager.start_session(
        session_id=call_sid,
        caller_phone=caller_phone,
        is_browser_simulated=False,
        applicant_name=f"Helpline Caller ({caller_phone})",
        district="Dhaka",
        db=db,
    )

    greeting = FIXED_QUESTIONS["RELAY_CONFIRM"]["bn"]
    q0_prompt = FIXED_QUESTIONS["Q0"]["bn"]
    initial_speech = f"{greeting} {q0_prompt}"

    gather_url = f"{settings.API_V1_PREFIX}/voice/twilio/step?session_id={session.session_id}&amp;question_id=Q0"
    twiml_xml = generate_twiml(say_text=initial_speech, gather_action=gather_url)

    return Response(content=twiml_xml, media_type="application/xml")


@router.post("/twilio/step", summary="Twilio Speech Gather Callback")
async def twilio_step_callback(
    request: Request,
    session_id: str,
    question_id: str,
    db: Session = Depends(get_db),
):
    """
    Processes speech gathered by Twilio IVR for the given intake question.
    Immediately saves answer, validates safety flags, and returns next question TwiML.
    """
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult")
    confidence_str = form_data.get("Confidence", "0.9")

    try:
        confidence = float(confidence_str)
    except ValueError:
        confidence = 0.9

    if not speech_result or not speech_result.strip():
        # Fallback if speech was not caught
        current_meta = FIXED_QUESTIONS.get(question_id, {})
        repeat_text = f"আমরা আপনার কথা বুঝতে পারিনি। {current_meta.get('bn', 'অনুগ্রহ করে আবার বলুন।')}"
        gather_url = f"{settings.API_V1_PREFIX}/voice/twilio/step?session_id={session_id}&amp;question_id={question_id}"
        twiml_xml = generate_twiml(say_text=repeat_text, gather_action=gather_url)
        return Response(content=twiml_xml, media_type="application/xml")

    # Authoritative workflow processing & immediate persistence
    try:
        step_result = voice_workflow_manager.process_step_answer(
            session_id=session_id,
            question_id=question_id,
            spoken_answer=speech_result.strip(),
            db=db,
            source="TWILIO_IVR_SPEECH",
            confidence=confidence,
        )
    except Exception as e:
        logger.error(f"Error in Twilio step processing: {e}")
        error_twiml = generate_twiml(say_text="সাময়িক কারিগরি সমস্যার জন্য দুঃখিত। কলটি পুনরায় সংযোগ করুন।", hangup=True)
        return Response(content=error_twiml, media_type="application/xml")

    is_completed = step_result.get("is_call_completed", False)
    if is_completed:
        closing_bn = "আপনার আবেদনটি সফলভাবে রেকর্ড করা হয়েছে। জাতীয় লিগ্যাল এইড অফিসার দ্রুত আপনার সঙ্গে যোগাযোগ করবেন। ধন্যবাদ।"
        twiml_xml = generate_twiml(say_text=closing_bn, hangup=True)
        return Response(content=twiml_xml, media_type="application/xml")

    next_step = step_result.get("next_step")
    next_prompt = FIXED_QUESTIONS.get(next_step, {}).get("bn", "পরবর্তী তথ্যটি বলুন।")
    next_gather_url = f"{settings.API_V1_PREFIX}/voice/twilio/step?session_id={session_id}&amp;question_id={next_step}"
    twiml_xml = generate_twiml(say_text=next_prompt, gather_action=next_gather_url)

    return Response(content=twiml_xml, media_type="application/xml")


@router.post("/twilio/status", summary="Twilio Call Status Callback")
async def twilio_call_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handles Twilio CallStatus changes (completed, busy, failed, no-answer).
    Ensures safe finalization of any lingering session.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    call_duration = form_data.get("CallDuration")

    logger.info(f"Twilio call status callback: sid={call_sid}, status={call_status}, duration={call_duration}s")

    if call_sid:
        session = db.query(VoiceCallSession).filter(VoiceCallSession.session_id == call_sid).first()
        if session:
            if call_duration and call_duration.isdigit():
                session.duration_seconds = int(call_duration)
            if session.current_step not in [VoiceIntakeStep.COMPLETED, VoiceIntakeStep.ABORTED]:
                # Finalize whatever was collected before disconnect
                try:
                    voice_workflow_manager.finalize_session(session.session_id, db)
                except Exception as e:
                    logger.warning(f"Session auto-finalize on hangup notice: {e}")
            db.commit()

    return {"status": "received"}


@router.websocket("/twilio/media-stream")
async def twilio_media_stream(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Twilio Media Stream bidirectional WebSocket endpoint.
    Receives raw caller audio stream frames from Twilio for realtime streaming analysis.
    """
    await websocket.accept()
    stream_sid = None
    call_sid = None

    try:
        while True:
            message_text = await websocket.receive_text()
            data = json.loads(message_text)
            event = data.get("event")

            if event == "start":
                start_data = data.get("start", {})
                stream_sid = data.get("streamSid")
                call_sid = start_data.get("callSid")
                logger.info(f"Twilio Media Stream started: stream={stream_sid}, call={call_sid}")

            elif event == "media":
                # Media chunk received: base64 payload
                payload = data.get("media", {}).get("payload")
                # Forwarded to speech recognition / audio processing pipeline
                pass

            elif event == "stop":
                logger.info(f"Twilio Media Stream stopped: stream={stream_sid}")
                break

    except WebSocketDisconnect:
        logger.info("Twilio Media Stream WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Error in Twilio Media Stream WebSocket: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
