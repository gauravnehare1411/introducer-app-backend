from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from models.user_models import UserInDB, TokenData
from config.database import users_collection, SECRET_KEY, ALGORITHM
import jwt


ACCESS_TOKEN_EXPIRE_SECONDS = 3600
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + expires_delta,
        "scope": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta):
    payload = data.copy()
    payload.update({
        "exp": datetime.utcnow() + expires_delta,
        "scope": "refresh"
    })
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_user(username: str):
    user_dict = await users_collection.find_one({"username": username})
    if user_dict:
        # Map database field 'password' to 'hashed_password'
        user_dict["hashed_password"] = user_dict.pop("password", None)
        user_dict["userId"] = user_dict.pop("_id", None)	
        return UserInDB(**user_dict)
    return None

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False	
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "access":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token scope. Use an access token."
            )
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)

    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user(username=token_data.username)

    if user is None:
        raise credentials_exception
    
    return user