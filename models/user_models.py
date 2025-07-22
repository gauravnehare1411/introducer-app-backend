from pydantic import BaseModel, EmailStr


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