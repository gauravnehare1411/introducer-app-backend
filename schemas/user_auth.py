from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from models.user_models import UserInDB, TokenData
from config.database import users_collection, SECRET_KEY, ALGORITHM
import jwt
import random
import string
import smtplib
from email.mime.text import MIMEText
from dotenv import find_dotenv, load_dotenv
import os

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)


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

async def get_user(email: str):
    user_dict = await users_collection.find_one({"email": email})
    if user_dict:
        # Map database field 'password' to 'hashed_password'
        user_dict["hashed_password"] = user_dict.pop("password", None)
        user_dict["userId"] = user_dict.pop("_id", None)	
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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


async def generate_unique_referral_id(name: str) -> str:
    while True:
        initials = ''.join([part[0].upper() for part in name.split() if part]) if name else 'XX'
        random_suffix = ''.join(random.choices(string.digits, k=4))
        referral_id = f"{initials}{random_suffix}"
        
        existing_user = await users_collection.find_one({"referralId": referral_id})
        if not existing_user:
            return referral_id
        

async def send_verification_email(to_email: str, code: str):
    sender_email = os.getenv("email_address")
    sender_password = os.getenv("email_password")
    subject = "Verify your email"
    body = f"Your verification code is: {code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    # Hostinger SMTP config
    smtp_server = "smtp.hostinger.com"
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send failed: {e}")