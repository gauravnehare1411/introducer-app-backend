from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    email: EmailStr | None = None  # was `username`


class RegisterUser(BaseModel):
    name: str | None = None
    email: EmailStr
    contactnumber: int | None = None
    password: str


class User(BaseModel):
    userId: str
    name: str | None = None
    email: EmailStr
    contactnumber: int | None = None
    referralId: str | None = None


class UserInDB(User):
    hashed_password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr
    contactnumber: int | None = None
