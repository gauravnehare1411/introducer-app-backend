from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: str | None = None

class RegisterUser(BaseModel):
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None
    password: str


class User(BaseModel):
    userId: str
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None

class UserInDB(User):
    hashed_password: str

class UserUpdate(BaseModel):
    username: str
    name: str | None = None
    email: str | None = None
    contactnumber: int | None = None