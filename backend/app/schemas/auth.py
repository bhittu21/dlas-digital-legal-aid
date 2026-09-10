from typing import Optional
import datetime
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    role: str
    district: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    full_name_bn: Optional[str] = None
    role: str = "applicant"
    phone_number: Optional[str] = None
    district: Optional[str] = None
    specialization: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    full_name_bn: Optional[str] = None
    role: str
    phone_number: Optional[str] = None
    district: Optional[str] = None
    specialization: Optional[str] = None
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class LawyerResponse(BaseModel):
    id: int
    full_name: str
    full_name_bn: Optional[str] = None
    district: Optional[str] = None
    specialization: Optional[str] = None
    phone_number: Optional[str] = None
    active_cases_count: int = 0

    class Config:
        from_attributes = True
