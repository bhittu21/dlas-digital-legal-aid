import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class VoiceSimulateStartRequest(BaseModel):
    caller_phone: Optional[str] = Field(default="+8801711000001", description="Phone number of the simulated incoming caller")
    applicant_name: Optional[str] = Field(default=None, description="Optional self-declared name")
    district: Optional[str] = Field(default="Dhaka", description="Simulated district")


class VoiceSimulateStartResponse(BaseModel):
    session_id: str
    case_id: int
    tracking_id: str
    current_step: str
    prompt_id: str
    prompt_text_bn: str
    prompt_text_en: str
    is_call_active: bool = True
    disclaimer: str = "Voice intake pipeline active. Answers are validated and stored immediately per turn."


class VoiceSimulateStepRequest(BaseModel):
    session_id: str = Field(..., description="Active voice session identifier")
    question_id: str = Field(..., description="ID of the question being answered (RELAY_CONFIRM, Q0, Q1, Q2, Q3)")
    spoken_answer: str = Field(..., description="Verbatim spoken transcript of the caller's answer")
    source: Optional[str] = Field(default="BROWSER_SIMULATED", description="CALLER_SPOKEN, BROWSER_SIMULATED, TWILIO_MEDIA_STREAM")
    confidence: Optional[float] = Field(default=1.0, description="Speech transcription confidence score (0.0 to 1.0)")


class VoiceAnswerResponse(BaseModel):
    id: int
    session_id: str
    case_id: Optional[int] = None
    question_id: str
    question: str
    answer: str
    source: str
    confidence: float
    danger_detected: bool
    danger_notes: Optional[str] = None
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceSimulateStepResponse(BaseModel):
    session_id: str
    case_id: int
    completed_question_id: str
    persisted_answer: VoiceAnswerResponse
    next_step: str
    next_prompt_text_bn: Optional[str] = None
    next_prompt_text_en: Optional[str] = None
    is_call_completed: bool = False
    danger_detected: bool = False
    risk_flags: List[str] = []
    suggested_priority: str = "MEDIUM"
    case_status: str = "AI_INTAKE"
    message_bn: str
    message_en: str


class VoiceSessionDetailResponse(BaseModel):
    id: int
    session_id: str
    caller_phone: Optional[str] = None
    current_step: str
    case_id: Optional[int] = None
    is_browser_simulated: bool
    danger_detected: bool
    risk_flags: List[str] = []
    suggested_priority: str
    safe_contact_time: Optional[str] = None
    answers: List[VoiceAnswerResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
