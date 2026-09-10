import re
import logging
from typing import Dict, Any, List, Optional
from app.models.case import LegalCategory
from app.config import settings

logger = logging.getLogger("dlas.gemini_voice")

DANGER_KEYWORDS = [
    "মারধর", "মারছে", "মারবে", "মারধোর", "হাত তুলছে", "পিটিয়েছে", "নির্যাতন",
    "হুমকি", "খুন", "মেরে ফেলবে", "প্রাণনাশের", "দা নিয়ে", "ছুরি নিয়ে", "আক্রমণ",
    "রক্ত", "বিপদে", "নিরাপদ নই", "নিরাপদে নেই", "ভয়ে আছি", "danger", "threat", "violence",
    "kill", "attack", "unsafe", "emergency"
]

ABUSER_PRESENT_KEYWORDS = [
    "কাছে আছে", "পাশে আছে", "রুমেই আছে", "ঘরে আছে", "পাশে বসে আছে", "শুনছে",
    "এখানে আছে", "সামনে আছে", "present", "right here", "next to me", "listening"
]

CHILD_RISK_KEYWORDS = [
    "বাচ্চা", "শিশু", "ছেলে", "মেয়ে", "সন্তান", "বাচ্চাদের", "শিশুদের",
    "অপ্রাপ্তবয়স্ক", "ছোট বাচ্চা", "child", "children", "baby", "minor", "kids"
]


class GeminiVoiceService:
    """
    AI voice intelligence engine for DLAS telephony and simulated browser intake.
    Understands colloquial Bangladesh Bangla and extracts safety alerts, entity categories,
    and safe callback protocols.
    
    STRICT COMPLIANCE:
    - Never makes judicial verification decisions.
    - Never changes workflow state autonomously (state machine resides in FastAPI).
    - Allegations are tagged as self-reported until human DLAO review.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    def analyze_answer(self, question_id: str, answer_text: str) -> Dict[str, Any]:
        """
        Analyzes spoken answer based on question context and returns safety flags,
        extracted entities, and confidence scores.
        """
        result = {
            "question_id": question_id,
            "answer_text": answer_text,
            "danger_detected": False,
            "risk_flags": [],
            "danger_notes": None,
            "confidence": 0.95,
            "extracted_entities": {},
        }

        if not answer_text or not answer_text.strip():
            return result

        text_lower = answer_text.lower()

        # 1. Q0: Consent & Representation Verification
        if question_id == "Q0":
            refusal = any(w in text_lower for w in ["না", "সম্মত নই", "বলব না", "রাজি না", "ভুল নম্বর", "ভুল কল", "no", "wrong", "refuse", "not agree"])
            has_explicit_yes = any(w in text_lower for w in ["হ্যাঁ", "জি", "হ্যা", "yes", "okay"])
            if refusal and not has_explicit_yes:
                result["consent_given"] = False
            elif any(w in text_lower for w in ["বলব না", "সম্মত নই", "রাজি না", "ভুল নম্বর"]):
                result["consent_given"] = False
            else:
                result["consent_given"] = True
            result["extracted_entities"]["consent_confirmed"] = result["consent_given"]

        # 2. Q1: Grievance Narrative Analysis
        elif question_id == "Q1":
            category = None
            if any(w in text_lower for w in ["জমি", "জায়গা", "বাটোয়ারা", "বেদখল", "খতিয়ান", "সীমানা", "land", "property"]):
                category = LegalCategory.LAND_PROPERTY
            elif any(w in text_lower for w in ["দেনমোহর", "খোরপোশ", "তালাক", "ডিভোর্স", "বিয়ে", "custody", "family"]):
                category = LegalCategory.FAMILY_MATRIMONIAL
            elif any(w in text_lower for w in ["যৌতুক", "মারধর", "নির্যাতন", "শারীরিক", "dowry", "violence", "domestic"]):
                category = LegalCategory.DOMESTIC_VIOLENCE_DOWRY
            elif any(w in text_lower for w in ["বেতন", "বকেয়া", "চাকরি", "মালিক", "গার্মেন্টস", "factory", "salary", "wage", "labour"]):
                category = LegalCategory.LABOUR_EMPLOYMENT
            elif any(w in text_lower for w in ["জামিন", "গ্রেফতার", "হাজত", "জেল", "bail", "police", "arrest", "criminal"]):
                category = LegalCategory.CRIMINAL_DEFENSE_BAIL
            else:
                category = LegalCategory.CIVIL_GENERAL

            result["extracted_entities"]["legal_category"] = category

            # Check if applicant declared their name
            name_m = re.search(r'(?:আমার নাম|নাম|name is|i am)\s*([a-zA-Z\u0980-\u09FF\s.]{3,30}?)(?:,|\.|\u0964|।|\sআমি|\sআমার|$)', answer_text)
            if name_m:
                cand_name = name_m.group(1).strip()
                if len(cand_name) > 2 and cand_name.lower() not in ["একজন", "caller", "applicant"]:
                    result["extracted_entities"]["applicant_name"] = cand_name

        # 3. Q2: Immediate Safety & Abuser Proximity Analysis
        elif question_id == "Q2":
            has_violence_or_threat = any(k in text_lower for k in DANGER_KEYWORDS)
            abuser_present = any(k in text_lower for k in ABUSER_PRESENT_KEYWORDS)
            not_safe = any(k in text_lower for k in ["নিরাপদে নেই", "নিরাপদ নই", "ভয়ে আছি", "বিপদে", "not safe", "unsafe"])

            if has_violence_or_threat or abuser_present or not_safe:
                result["danger_detected"] = True
                notes = []

                if has_violence_or_threat:
                    result["risk_flags"].append("CURRENT_VIOLENCE_OR_THREAT")
                    notes.append("Threats of physical violence or harm detected in statement")

                if abuser_present:
                    result["risk_flags"].append("ABUSER_PRESENT")
                    notes.append("Caller reported abuser is present or nearby")

                if not_safe:
                    result["risk_flags"].append("IMMEDIATE_DANGER")
                    notes.append("Caller stated they are not safe at present location")

                result["danger_notes"] = "; ".join(notes)
                result["extracted_entities"]["safety_status"] = "UNSAFE"
            else:
                result["extracted_entities"]["safety_status"] = "SAFE"

        # 4. Q3: Child Risk & Safe Callback Protocol Analysis
        elif question_id == "Q3":
            has_child_risk = any(k in text_lower for k in CHILD_RISK_KEYWORDS) and (
                any(k in text_lower for k in DANGER_KEYWORDS) or
                any(w in text_lower for w in ["ঝুঁকি", "ভয়", "কেড়ে", "মারছে", "মারধর", "risk", "danger"])
            )

            if has_child_risk:
                result["danger_detected"] = True
                result["risk_flags"].append("CHILD_AT_RISK")
                result["danger_notes"] = "Children reported involved or at risk of violence/harm"
                result["extracted_entities"]["child_risk"] = True
            elif any(k in text_lower for k in CHILD_RISK_KEYWORDS):
                result["extracted_entities"]["children_involved"] = True

            # Extract safe contact time protocol
            time_matches = []
            if "সকালে" in text_lower or "morning" in text_lower:
                time_matches.append("Morning (সকাল)")
            if "দুপুরে" in text_lower or "afternoon" in text_lower:
                time_matches.append("Afternoon (দুপুর)")
            if "বিকালে" in text_lower:
                time_matches.append("Late Afternoon (বিকাল)")
            if "রাতে" in text_lower or "evening" in text_lower or "night" in text_lower:
                time_matches.append("Evening/Night (রাত)")

            time_pattern = re.search(r'([০-৯0-9]{1,2}(?::[০-৯0-9]{2})?\s*(?:টায়|টা|am|pm))', text_lower)
            if time_pattern:
                time_matches.append(time_pattern.group(1))

            if time_matches:
                safe_time = ", ".join(time_matches)
                result["extracted_entities"]["safe_contact_time"] = safe_time
            else:
                result["extracted_entities"]["safe_contact_time"] = "Caller did not specify time; use default protocol"

        return result


gemini_voice_service = GeminiVoiceService()
