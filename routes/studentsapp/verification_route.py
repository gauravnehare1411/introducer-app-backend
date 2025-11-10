from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from models.students_models.auth_models import Token, RefreshTokenRequest, RegisterUser, ALLOWED_ROLES, EmailOnlyRequest
from schemas.student_auth.auth_schema import authenticate_user, ACCESS_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_DAYS, generate_tokens, hash_password
from datetime import datetime, timedelta
from config.ahatin_conf.students_db import users_collection, verification_collection
from schemas.student_auth.send_emails import send_verification_email
import jwt
import random
import uuid

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def start_registration(request: RegisterUser, background_tasks: BackgroundTasks):
    """
    Start user registration process by sending verification code
    """
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

        await verification_collection.delete_one({"_id": request.email})

        verification_code = str(random.randint(100000, 999999))

        verification_data = {
            "_id": request.email,
            "name": request.name,
            "contactnumber": request.contactnumber,
            "password": hash_password(request.password),
            "code": verification_code,
            "roles": request.roles,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "created_at": datetime.utcnow()
        }

        await verification_collection.insert_one(verification_data)

        # Send verification email in background
        background_tasks.add_task(send_verification_email, request.email, verification_code)

        return {
            "message": "Verification code sent to your email.",
            "email": request.email,
            "expires_in": "5 minutes"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during registration. Please try again."
        )


@router.post("/verify-code", response_model=Token)
async def verify_code(
    email: str = Form(..., description="User email address"),
    code: str = Form(..., description="6-digit verification code")
):
    try:
        email = email.lower()
        verification = await verification_collection.find_one({"_id": email})

        if not verification:
            raise HTTPException(
                status_code=400, 
                detail="No verification request found. Please register first."
            )

        if verification["code"] != code:
            raise HTTPException(
                status_code=400, 
                detail="Invalid verification code."
            )

        if verification["expires_at"] < datetime.utcnow():
            await verification_collection.delete_one({"_id": email})
            raise HTTPException(
                status_code=400, 
                detail="Verification code has expired. Please request a new one."
            )

        existing_user = await users_collection.find_one({"email": email})
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already registered with this email."
            )
        
        else:
            user_data = {
                "_id": str(uuid.uuid4()),
                "userId": str(uuid.uuid4()),
                "name": verification["name"],
                "email": email,
                "contactnumber": verification["contactnumber"],
                "password": verification["password"],
                "roles": verification["roles"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "email_verified": True
            }
            await users_collection.insert_one(user_data)

        # Clean up verification data
        await verification_collection.delete_one({"_id": email})

        user = await users_collection.find_one({"email": email})

        if not user:
            print("err")
            raise HTTPException(status_code=500, detail="User creation failed.")

        roles = user.get("roles", [])
        user_id = user.get("userId")

        access_token, refresh_token = generate_tokens(user.get('email'), roles)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
            roles=roles
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during verification. Please try again."
        )
    
@router.post("/resend-code")
async def resend_code(request: EmailOnlyRequest, background_tasks: BackgroundTasks):
    try:
        request.email = request.email.lower()

        existing = await verification_collection.find_one({"_id": request.email})
        if not existing:
            raise HTTPException(status_code=400, detail="No verification request found. Please register again.")

        if datetime.utcnow() <= existing["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP is still valid. Please check your email.")

        new_code = str(random.randint(100000, 999999))
        await verification_collection.update_one(
            {"_id": request.email},
            {"$set": {"code": new_code, "expires_at": datetime.utcnow() + timedelta(minutes=5)}}
        )

        background_tasks.add_task(send_verification_email, request.email, new_code)
        return {"message": "A new verification code has been sent."}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")