from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    role: str


class TokenData(BaseModel):
    email: EmailStr | None = None
    role: str | None = None


class RegisterUser(BaseModel):
    name: str | None = None
    email: EmailStr
    contactnumber: str | None = None
    password: str


class User(BaseModel):
    userId: str
    name: str | None = None
    email: EmailStr
    contactnumber: str | None = None
    referralId: str | None = None
    role: str


class UserInDB(User):
    hashed_password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr
    contactnumber: str | None = None

class EmailOnlyRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    contactnumber: Optional[str] = None

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    contactnumber: Optional[str] = None


ALLOWED_REFERRAL_STATUSES = {"Pending", "Approved", "Rejected"}

def _normalize_status(value: str) -> str:
    """Normalize inputs like 'pending', 'PENDING' -> 'Pending'."""
    return value.strip().capitalize()
