from typing import Optional
from pydantic import BaseModel, Field


class NIDVerifyRequest(BaseModel):
    nid_number: str = Field(..., min_length=10, max_length=17, description="10-digit Smart NID or 13/17-digit Legacy NID")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    name: Optional[str] = None


class NIDVerifyResponse(BaseModel):
    is_valid: bool
    nid_number: str
    name_en: Optional[str] = None
    name_bn: Optional[str] = None
    father_name: Optional[str] = None
    district: Optional[str] = None
    mode: str = "DEMO_MOCK_ADAPTER"
    disclaimer: str = "Demo/simulated identity verification. No connection to live government servers is claimed or utilized."
