import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class VoiceIntakeStep:
    CALL_STARTED = "CALL_STARTED"
    RELAY_CONFIRM = "RELAY_CONFIRM"
    Q0 = "Q0"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"

    ALL_STEPS = [CALL_STARTED, RELAY_CONFIRM, Q0, Q1, Q2, Q3, COMPLETED, ABORTED]


# Standard Bangla intake prompts controlled strictly by the backend
FIXED_QUESTIONS = {
    "RELAY_CONFIRM": {
        "id": "RELAY_CONFIRM",
        "bn": "জাতীয় আইনগত সহায়তা হেল্পলাইনে স্বাগতম। এটি একটি সরকারি আইনগত সহায়তা সেবা। আমাদের কথোপকথন রেকর্ড করা হতে পারে।",
        "en": "Welcome to the National Legal Aid Helpline. This is an official legal aid service. This call may be recorded for quality and case records.",
    },
    "Q0": {
        "id": "Q0",
        "bn": "যার জন্য আইনগত সহায়তা প্রয়োজন, তিনি কি এই কলে আছেন এবং নিজের সমস্যাটি সম্পর্কে কথা বলতে সম্মত?",
        "en": "Is the person who requires legal aid present on this call and consenting to speak about their issue?",
        "is_mandatory": True,
    },
    "Q1": {
        "id": "Q1",
        "bn": "আপনার সমস্যাটি সংক্ষেপে বলবেন?",
        "en": "Could you please briefly describe your legal problem?",
        "is_mandatory": True,
    },
    "Q2": {
        "id": "Q2",
        "bn": "আপনি কি এই মুহূর্তে নিরাপদে আছেন? আপনার স্বামী বা যিনি আপনাকে হুমকি দিচ্ছেন, তিনি কি এখন আপনার কাছে আছেন?",
        "en": "Are you safe right now? Is your husband or the person threatening you near you at this moment?",
        "is_mandatory": True,
    },
    "Q3": {
        "id": "Q3",
        "bn": "কোনো শিশু এই সমস্যার সঙ্গে জড়িত বা ঝুঁকিতে আছে কি? আর ভবিষ্যতে আপনার সঙ্গে যোগাযোগ করার নিরাপদ সময় বা উপায় কী?",
        "en": "Are any children involved or at risk in this matter? And what is a safe time or method to contact you in the future?",
        "is_mandatory": True,
    },
}


class VoiceCallSession(Base):
    __tablename__ = "voice_call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    caller_phone = Column(String(50), nullable=True, index=True)
    current_step = Column(String(50), default=VoiceIntakeStep.CALL_STARTED, nullable=False)

    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    is_browser_simulated = Column(Boolean, default=False)
    consent_given = Column(Boolean, nullable=True)

    # Risk & Danger Evaluation
    danger_detected = Column(Boolean, default=False, index=True)
    risk_flags = Column(JSON, default=list)  # e.g. ["IMMEDIATE_DANGER", "ABUSER_PRESENT", "CHILD_AT_RISK"]
    suggested_priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, EMERGENCY
    safe_contact_time = Column(String(255), nullable=True)

    # Call Metadata
    duration_seconds = Column(Integer, default=0)
    audio_recording_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    answers = relationship("VoiceIntakeAnswer", back_populates="session", cascade="all, delete-orphan", order_by="VoiceIntakeAnswer.id")
    case = relationship("Case", foreign_keys=[case_id])


class VoiceIntakeAnswer(Base):
    __tablename__ = "voice_intake_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("voice_call_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)

    question_id = Column(String(50), nullable=False)  # Q0, Q1, Q2, Q3
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source = Column(String(50), default="CALLER_SPOKEN")  # CALLER_SPOKEN, BROWSER_SIMULATED, TWILIO_MEDIA_STREAM

    confidence = Column(Float, default=1.0)
    danger_detected = Column(Boolean, default=False)
    danger_notes = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    session = relationship("VoiceCallSession", back_populates="answers")
    case = relationship("Case", foreign_keys=[case_id])
