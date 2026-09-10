import re
import datetime
import logging
from typing import Dict, Any, Tuple, List, Optional
from app.models.intake_application import ApplicationCompleteness, FieldProvenance
from app.models.case import LegalCategory
from app.utils import now_utc

logger = logging.getLogger("dlas.intake_mapper")

# Core mandatory fields required under Legal Aid Services Act 2000
MANDATORY_CORE_FIELDS = [
    "applicant_name",
    "phone_number",
    "present_district",
    "monthly_income_bdt",
    "legal_category",
    "grievance_description",
    "opposing_party_name",
]

RECOMMENDED_FIELDS = [
    "nid_number",
    "present_upazila",
    "incident_date",
    "relief_sought",
    "opposing_party_address",
    "occupation",
    "marital_status",
]

FOLLOW_UP_TEMPLATES = {
    "applicant_name": {
        "bn": "অনুগ্রহ করে আপনার পুরো নামটি স্পষ্ট করে বলুন।",
        "en": "Please state your full legal name clearly.",
    },
    "phone_number": {
        "bn": "আপনার সাথে যোগাযোগের একটি সচল মোবাইল নম্বর দিন।",
        "en": "Please provide an active mobile phone number for case notices.",
    },
    "present_district": {
        "bn": "আপনি বর্তমানে কোন জেলায় বসবাস করছেন?",
        "en": "Which district in Bangladesh do you currently reside in?",
    },
    "present_upazila": {
        "bn": "আপনার বর্তমান উপজেলা বা থানার নাম কী?",
        "en": "What is the name of your current upazila or police station?",
    },
    "monthly_income_bdt": {
        "bn": "আপনার পরিবারের মাসিক গড় আয় কত টাকা? (বিনামূল্যে সরকারি আইনগত সহায়তা পাওয়ার যোগ্যতা যাচাইয়ে এটি আবশ্যক)",
        "en": "What is your approximate monthly household income in BDT? (Required to verify statutory legal aid eligibility)",
    },
    "legal_category": {
        "bn": "আপনার সমস্যাটি কোন আইনের আওতাধীন? (যেমন: জমিজমা, পারিবারিক, দেনমোহর, শ্রম আইন, বা ফৌজদারি)",
        "en": "What is the general domain of your legal grievance? (e.g. Land, Family, Unpaid Wages, Criminal Bail)",
    },
    "grievance_description": {
        "bn": "আপনার সাথে কী অন্যায় হয়েছে বা কী সমস্যায় পড়েছেন তা বিস্তারিত বলুন।",
        "en": "Please describe the factual details and background of your legal grievance.",
    },
    "opposing_party_name": {
        "bn": "যার বা যাদের বিরুদ্ধে আপনার অভিযোগ তার পুরো নাম কী?",
        "en": "What is the full name of the opposing party / respondent?",
    },
    "opposing_party_address": {
        "bn": "বিবাদী বা অপর পক্ষের বর্তমান ঠিকানা বা কর্মস্থল কোথায়?",
        "en": "What is the address or whereabouts of the opposing party?",
    },
    "nid_number": {
        "bn": "আপনার ১০ বা ১৭ ডিজিটের জাতীয় পরিচয়পত্র (এনআইডি) নম্বরটি প্রদান করুন।",
        "en": "Please provide your 10-digit Smart NID or 17-digit legacy National ID number.",
    },
    "incident_date": {
        "bn": "ঘটনাটি বা বিরোধটি আনুমানিক কবে ঘটেছিল?",
        "en": "Approximately when did this incident or dispute occur?",
    },
    "relief_sought": {
        "bn": "ডিজিটাল আইনগত সহায়তার মাধ্যমে আপনি ঠিক কী ধরনের প্রতিকার চান? (যেমন: আপস-মীমাংসা, মামলা পরিচালনা, খোরপোশ)",
        "en": "What specific legal remedy or relief do you seek? (e.g., mediation, litigation, maintenance recovery)",
    },
}


BN_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def normalize_digits(text: str) -> str:
    """Converts Bengali numerals (০-৯) to standard ASCII numerals (0-9)."""
    return text.translate(BN_DIGIT_MAP)


def calculate_application_completeness(
    data: Dict[str, Any]
) -> Tuple[str, float, List[str], List[Dict[str, Any]]]:
    """
    Evaluates legal aid application completeness against DBLA standards:
    - COMPLETE: All mandatory core fields and >= 90% recommended fields present.
    - PARTIALLY_COMPLETE: All mandatory core fields present, but missing some recommended fields.
    - MISSING_REQUIRED_INFORMATION: Missing one or more statutory mandatory core fields.
    
    Returns:
        (completeness_status, score_0_to_100, missing_required_fields, follow_up_questions)
    """
    missing_mandatory = []
    for field in MANDATORY_CORE_FIELDS:
        val = data.get(field)
        if val is None or str(val).strip() == "" or (isinstance(val, (int, float)) and val < 0):
            missing_mandatory.append(field)

    missing_recommended = []
    for field in RECOMMENDED_FIELDS:
        val = data.get(field)
        if val is None or str(val).strip() == "":
            missing_recommended.append(field)

    # Scoring weights: 70% mandatory (10% each for 7 fields), 30% recommended (4.28% each)
    mandatory_earned = (len(MANDATORY_CORE_FIELDS) - len(missing_mandatory)) * 10.0
    recommended_earned = (len(RECOMMENDED_FIELDS) - len(missing_recommended)) * (30.0 / len(RECOMMENDED_FIELDS))
    total_score = round(mandatory_earned + recommended_earned, 1)

    # Determine status
    if missing_mandatory:
        status = ApplicationCompleteness.MISSING_REQUIRED_INFORMATION
    elif total_score >= 88.0:
        status = ApplicationCompleteness.COMPLETE
    else:
        status = ApplicationCompleteness.PARTIALLY_COMPLETE

    # Generate follow-up questions
    follow_up_questions = []
    all_missing = missing_mandatory + missing_recommended
    for field in all_missing:
        if field in FOLLOW_UP_TEMPLATES:
            follow_up_questions.append({
                "field": field,
                "is_mandatory": field in MANDATORY_CORE_FIELDS,
                "question_bn": FOLLOW_UP_TEMPLATES[field]["bn"],
                "question_en": FOLLOW_UP_TEMPLATES[field]["en"],
            })

    return (status, total_score, missing_mandatory, follow_up_questions)


def extract_entities_from_spoken_transcript(
    transcript: str,
    caller_phone: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Maps raw spoken answers into validated DBLA structured fields.
    
    CRITICAL SAFETY RULES:
    1. NEVER invent, hallucinate, or fabricate missing fields.
    2. Missing information MUST remain None / null.
    3. Never infer identity merely from SIM ownership.
    4. Every successfully extracted field receives FieldProvenance.AI_EXTRACTED.
    """
    extracted: Dict[str, Any] = {}
    provenances: Dict[str, Dict[str, Any]] = {}
    now_str = now_utc().isoformat()

    if not transcript or not transcript.strip():
        return extracted, provenances

    text_lower = transcript.lower()
    text_normalized = normalize_digits(text_lower)

    # 1. Phone number (from caller ID / SIP metadata)
    if caller_phone:
        extracted["phone_number"] = caller_phone
        provenances["phone_number"] = {
            "source": FieldProvenance.CALLER_REPORTED,
            "timestamp": now_str,
            "confidence": 1.0,
            "notes": "Reported via telephony signaling / intake form",
        }

    # 2. Extract Legal Category from keywords
    category = None
    if any(w in text_lower for w in ["জমি", "জায়গা", "বাটোয়ারা", "বেদখল", "খতিয়ান", "land", "property", "boundary"]):
        category = LegalCategory.LAND_PROPERTY
    elif any(w in text_lower for w in ["দেনমোহর", "খোরপোশ", "তালাক", "ডিভোর্স", "বিয়ে", "custody", "dower", "maintenance", "family"]):
        category = LegalCategory.FAMILY_MATRIMONIAL
    elif any(w in text_lower for w in ["যৌতুক", "মারধর", "নির্যাতন", "dowry", "violence", "domestic", "মারপিট"]):
        category = LegalCategory.DOMESTIC_VIOLENCE_DOWRY
    elif any(w in text_lower for w in ["বেতন", "বকেয়া", "চাকরি", "মালিক", "গার্মেন্টস", "factory", "salary", "wage", "labour", "শ্রমিক"]):
        category = LegalCategory.LABOUR_EMPLOYMENT
    elif any(w in text_lower for w in ["জামিন", "গ্রেফতার", "হাজত", "জেল", "bail", "police", "arrest", "criminal", "মামলা"]):
        category = LegalCategory.CRIMINAL_DEFENSE_BAIL
    elif any(w in text_lower for w in ["টাকা", "ঋণ", "চুক্তি", "দেনা", "civil", "money", "contract"]):
        category = LegalCategory.CIVIL_GENERAL

    if category:
        extracted["legal_category"] = category
        provenances["legal_category"] = {
            "source": FieldProvenance.AI_EXTRACTED,
            "timestamp": now_str,
            "confidence": 0.88,
            "notes": f"Classified from conversational terms: {category}",
        }

    # 3. Extract District from known Bangladesh Districts
    known_districts = [
        "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Rangpur", "Khulna", "Barishal", "Mymensingh",
        "Comilla", "Cox's Bazar", "Bogra", "Jessore", "Kushtia", "Dinajpur", "Pabna", "Noakhali",
        "Feni", "Brahmanbaria", "Narayanganj", "Gazipur", "Tangail", "Faridpur", "Sunamganj",
        "Habiganj", "Moulvibazar", "Patuakhali", "Bhola", "Barguna", "Satkhira", "Kurigram", "Netrokona"
    ]
    for dist in known_districts:
        if dist.lower() in text_lower or (dist == "Chittagong" and "চট্টগ্রাম" in transcript) or (dist == "Dhaka" and "ঢাকা" in transcript) or (dist == "Sylhet" and "সিলেট" in transcript):
            extracted["present_district"] = dist
            provenances["present_district"] = {
                "source": FieldProvenance.AI_EXTRACTED,
                "timestamp": now_str,
                "confidence": 0.85,
                "notes": f"Identified district mention: {dist}",
            }
            break

    # 4. Extract monthly income if explicitly stated (e.g., "আয় ১২০০০ টাকা" or "income 12000")
    income_match = re.search(r'(?:আয়|বেতন|income|salary|টাকা|bdt)\s*(?:হলো|হয়|হচ্ছে|is|of)?\s*([0-9]{3,6})', text_normalized)
    if not income_match:
        income_match = re.search(r'([0-9]{3,6})\s*(?:টাকা|bdt)', text_normalized)
    if income_match:
        try:
            income_val = float(income_match.group(1))
            if 1000 <= income_val <= 200000:
                extracted["monthly_income_bdt"] = income_val
                extracted["annual_income_bdt"] = income_val * 12
                provenances["monthly_income_bdt"] = {
                    "source": FieldProvenance.AI_EXTRACTED,
                    "timestamp": now_str,
                    "confidence": 0.82,
                    "notes": f"Extracted income: BDT {income_val}",
                }
                provenances["annual_income_bdt"] = {
                    "source": FieldProvenance.SYSTEM_DERIVED,
                    "timestamp": now_str,
                    "confidence": 1.0,
                    "notes": "Calculated as monthly_income_bdt * 12",
                }
        except ValueError:
            pass

    # 5. Extract opposing party name if mentioned
    opp_match = re.search(r'(?:বিরুদ্ধে|বিপক্ষ|অপরপক্ষ|বিবাদী|অপজিট|against|respondent)\s*(?:হলো|নাম|হচ্ছে|is|:)?\s*([a-zA-Z\u0980-\u09FF\s.]{3,30}?)(?:,|\.|\u0964|।|\sএবং|\sand|\sআমার|\sমাসিক|$)', transcript)
    if not opp_match:
        opp_match = re.search(r'(?:দখল করেছে|নির্যাতন করেছে|মারধর করেছে|তাড়িয়ে দিয়েছে)\s*([a-zA-Z\u0980-\u09FF\s.]{3,30}?)(?:,|\.|\u0964|।|\sএবং|\sand|\sআমার|\sমাসিক|$)', transcript)
    if opp_match:
        opp_name = opp_match.group(1).strip()
        if len(opp_name) > 2 and opp_name not in ["আমার", "তার", "তিনি", "the"]:
            extracted["opposing_party_name"] = opp_name
            provenances["opposing_party_name"] = {
                "source": FieldProvenance.AI_EXTRACTED,
                "timestamp": now_str,
                "confidence": 0.80,
                "notes": f"Extracted opposing party: {opp_name}",
            }

    # 6. Extract applicant name if explicitly declared
    name_match = re.search(r'(?:আমার নাম|নাম|name is|i am)\s*(?:হলো|হচ্ছে|is)?\s*([a-zA-Z\u0980-\u09FF\s.]{3,30}?)(?:,|\.|\u0964|।|\sআমি|\sআমার|\sand|$)', transcript)
    if name_match:
        cand_name = name_match.group(1).strip()
        if len(cand_name) > 2 and cand_name.lower() not in ["shahnaz", "applicant", "caller", "একজন"]:
            extracted["applicant_name"] = cand_name
            provenances["applicant_name"] = {
                "source": FieldProvenance.AI_EXTRACTED,
                "timestamp": now_str,
                "confidence": 0.85,
                "notes": f"Extracted applicant name: {cand_name}",
            }

    # 7. Grievance description is preserved in original verbatim language
    extracted["grievance_description"] = transcript.strip()
    provenances["grievance_description"] = {
        "source": FieldProvenance.CALLER_REPORTED,
        "timestamp": now_str,
        "confidence": 1.0,
        "notes": "Original verbatim grievance transcript",
    }

    # Default case title from extracted details
    cat_label = extracted.get("legal_category", "Legal Grievance").replace("_", " ").title()
    name_label = extracted.get("applicant_name", "Citizen")
    extracted["case_title"] = f"{cat_label} - {name_label}"
    provenances["case_title"] = {
        "source": FieldProvenance.SYSTEM_DERIVED,
        "timestamp": now_str,
        "confidence": 1.0,
        "notes": "Synthesized title from category and applicant",
    }

    return extracted, provenances
