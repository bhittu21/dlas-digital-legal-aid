import re
from typing import Dict, Any
from app.schemas.nid import NIDVerifyRequest, NIDVerifyResponse

# Realistic sample mock records for deterministic demo verification
MOCK_NID_REGISTRY = {
    "19852691234567890": {
        "name_en": "Khadija Begum",
        "name_bn": "খাদিজা বেগম",
        "father_name": "Abdul Latif",
        "district": "Dhaka",
    },
    "1234567890": {
        "name_en": "Rashidul Islam",
        "name_bn": "রাশিদুল ইসলাম",
        "father_name": "Mojibur Rahman",
        "district": "Chittagong",
    },
    "9876543210": {
        "name_en": "Salma Khatun",
        "name_bn": "সালমা খাতুন",
        "father_name": "Kashem Ali",
        "district": "Sylhet",
    },
}

DISTRICT_LIST = [
    "Dhaka", "Chittagong", "Rajshahi", "Khulna", "Barishal", "Sylhet", "Rangpur", "Mymensingh",
    "Comilla", "Gazipur", "Narayanganj", "Bogra", "Jessore", "Dinajpur", "Cox's Bazar"
]


class MockNIDAdapter:
    """
    Mock/Demo Identity Adapter for Bangladesh National ID verification.
    
    CRITICAL TRANSPARENCY:
    DLAS does NOT claim or possess direct access to the live Election Commission
    or Porichoy NID database. This adapter validates standard NID format rules
    and provides simulated demographic hydration strictly for prototyping,
    testing, and legal-aid demonstration purposes.
    """

    @staticmethod
    def verify_nid(req: NIDVerifyRequest) -> NIDVerifyResponse:
        nid = req.nid_number.strip()
        dob = req.date_of_birth.strip()

        # Format validation:
        # Smart NID: exactly 10 digits
        # Old NID: 13 digits or 17 digits (13 prepended with 4-digit birth year)
        is_smart = bool(re.match(r"^\d{10}$", nid))
        is_legacy = bool(re.match(r"^\d{13}$|^\d{17}$", nid))

        if not (is_smart or is_legacy):
            return NIDVerifyResponse(
                is_valid=False,
                nid_number=nid,
                mode="DEMO_MOCK_ADAPTER",
                disclaimer="Simulated verification failed: NID must be 10 digits (Smart) or 13/17 digits (Legacy)."
            )

        # If present in pre-configured registry, return deterministic record
        if nid in MOCK_NID_REGISTRY:
            data = MOCK_NID_REGISTRY[nid]
            return NIDVerifyResponse(
                is_valid=True,
                nid_number=nid,
                name_en=data["name_en"],
                name_bn=data["name_bn"],
                father_name=data["father_name"],
                district=data["district"],
                mode="DEMO_MOCK_ADAPTER",
                disclaimer="Simulated for demonstration; no actual government database connection."
            )

        # Otherwise synthesize consistent demo data from NID digits
        digit_sum = sum(int(d) for d in nid if d.isdigit())
        district = DISTRICT_LIST[digit_sum % len(DISTRICT_LIST)]
        simulated_name = req.name or f"Citizen (NID ending in {nid[-4:]})"

        return NIDVerifyResponse(
            is_valid=True,
            nid_number=nid,
            name_en=simulated_name,
            name_bn=f"নাগরিক ({nid[-4:]})",
            father_name="Late Golam Kibria",
            district=district,
            mode="DEMO_MOCK_ADAPTER",
            disclaimer="Simulated for demonstration; no actual government database connection."
        )
