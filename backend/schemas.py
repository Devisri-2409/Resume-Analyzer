from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AdminInitRequest(BaseModel):
    full_name: str = Field(default="Platform Administrator", min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    bio: Optional[str] = None


class EducationCreateRequest(BaseModel):
    degree: str = Field(min_length=1, max_length=150)
    branch: Optional[str] = ""
    college: Optional[str] = ""
    graduation_year: Optional[str] = ""


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = ""
    technologies: Optional[str] = ""
    github_url: Optional[str] = ""
    live_url: Optional[str] = ""


class CertificationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    issuing_organization: Optional[str] = ""
    issue_date: Optional[str] = ""
    credential_url: Optional[str] = ""


class SkillAddRequest(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)


class QuizSubmitRequest(BaseModel):
    answers: Dict[int, int]  # question_id -> option_id


class EmailVerifyRequest(BaseModel):
    token: str = Field(min_length=10, max_length=255)


class PhoneSendOtpRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=50)


class PhoneVerifyOtpRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=50)
    otp: str = Field(min_length=4, max_length=10)

