from datetime import datetime, timedelta
from typing import Annotated, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from models.students_models.auth_models import UserInDB, TokenData
from config.ahatin_conf.students_db import users_collection
from config.ahatin_conf.get_studentenv_var import AHATIN_SECRET_KEY, AHATIN_ALGORITHM
import jwt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

ACCESS_TOKEN_EXPIRE_SECONDS = 3600
REFRESH_TOKEN_EXPIRE_DAYS = 7


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
    return jwt.encode(to_encode, AHATIN_SECRET_KEY, algorithm=AHATIN_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta):
    payload = data.copy()
    payload.update({
        "exp": datetime.utcnow() + expires_delta,
        "scope": "refresh"
    })
    return jwt.encode(payload, AHATIN_SECRET_KEY, algorithm=AHATIN_ALGORITHM)

def generate_tokens(email: str, roles: list):
    access_token = create_access_token(
        data={"sub": email, "roles": roles},
        expires_delta=timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    )
    refresh_token = create_refresh_token(
        data={"sub": email, "roles": roles},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return access_token, refresh_token

async def get_user(email: str):
    user_dict = await users_collection.find_one({"email": email})
    if user_dict:
        user_dict["hashed_password"] = user_dict.get("password")
        
        user_dict["userId"] = user_dict.get("userId")
        
        if "roles" in user_dict and not isinstance(user_dict["roles"], list):
            user_dict["roles"] = [user_dict["roles"]]
        
        return UserInDB(**user_dict)
    return None

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
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
        payload = jwt.decode(token, AHATIN_SECRET_KEY, algorithms=[AHATIN_ALGORITHM])
        if payload.get("scope") != "access":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token scope. Use an access token."
            )
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)

    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user(email=token_data.email)

    if user is None:
        raise credentials_exception
    
    return user

def requires_roles(allowed_roles: List[str]):
    async def role_checker(current_user: UserInDB = Depends(get_current_user)):
        user_roles = current_user.roles if current_user.roles else []
        
        if not any(role.lower() in [r.lower() for r in allowed_roles] for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker