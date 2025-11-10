from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from models.students_models.auth_models import Token, RefreshTokenRequest, RegisterUser, ALLOWED_ROLES, ForgotPasswordRequest, SecurityQuestionsVerify, ResetPasswordRequest
from schemas.student_auth.auth_schema import authenticate_user, ACCESS_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_DAYS, generate_tokens, hash_password
from datetime import datetime, timedelta
from jose import JWTError
from config.ahatin_conf.get_studentenv_var import AHATIN_SECRET_KEY, AHATIN_ALGORITHM
from config.ahatin_conf.students_db import users_collection, verification_collection
from schemas.student_auth.send_emails import send_verification_email
import jwt
import random
import uuid

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_202_ACCEPTED)
async def start_registration(request: RegisterUser):
    try:
        request.email = request.email.lower()
        for role in request.roles:
            if role.lower() not in ALLOWED_ROLES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role '{role}'. Allowed roles: {list(ALLOWED_ROLES)}"
                )

        existing_user = await users_collection.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User already exist."
            )
        print(hash_password(request.password))

        user_dict = {
            "_id": str(uuid.uuid4()),
            "userId": str(uuid.uuid4()),
            "name": request.name,
            "email": request.email,
            "contactnumber": request.contactnumber,
            "password": hash_password(request.password),
            "roles": request.roles,
            "security_questions": {
                "first_school": request.security_questions.first_school,
                "dob": request.security_questions.date_of_birth
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        await users_collection.insert_one(user_dict)

        access_token, refresh_token = generate_tokens(request.email, request.roles)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
            roles=request.roles
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during registration. Please try again."
        )
    

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
)-> Token:
    
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW.Authenticate": "Bearer"}
        )

    access_token, refresh_token = generate_tokens(user.email, user.roles)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        roles=user.roles
    )


@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    try:
        refresh_token = request.refresh_token
        
        payload = jwt.decode(refresh_token, AHATIN_SECRET_KEY, algorithms=[AHATIN_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        token_scope = payload.get("scope")
        if token_scope != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")

        user = await users_collection.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        access_token, new_refresh_token = generate_tokens(user.get("email"), user.get("roles"))

        return Token(
            access_token=access_token, 
            refresh_token=new_refresh_token, 
            token_type="bearer", 
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS, 
            roles=user.get("roles")
        )

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


from fastapi import HTTPException, status

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email.lower()
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User with this email does not exist."
        )
    
    return {"message": "User found. Please answer security questions."}

@router.post("/verify-security-questions")
async def verify_security_questions(request: SecurityQuestionsVerify):
    email = request.email.lower()
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if (user["security_questions"]["first_school"].lower() != request.first_school.lower()
        or user["security_questions"]["dob"] != request.dob):
        raise HTTPException(status_code=400, detail="Incorrect security answers.")

    return {"message": "Security questions verified. You can reset your password."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    email = request.email.lower()
    hashed_password = hash_password(request.new_password)

    result = await users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Password reset failed.")
    
    return {"message": "Password has been successfully reset."}
