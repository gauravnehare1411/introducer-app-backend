import uuid
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from models.user_models import Token, RegisterUser, EmailOnlyRequest, ALLOWED_ROLES
from schemas.user_auth import *
from config.database import users_collection, verification_collection
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from schemas.send_emails import send_verification_email


router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def start_registration(request: RegisterUser, background_tasks: BackgroundTasks):
    """
    Start user registration process by sending verification code
    """
    try:
        request.email = request.email.lower()
        print(request)
        # Validate roles
        for role in request.roles:
            if role.lower() not in ALLOWED_ROLES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role '{role}'. Allowed roles: {list(ALLOWED_ROLES)}"
                )

        # Check if user exists with any of the requested roles
        existing_user = await users_collection.find_one({"email": request.email})
        if existing_user:
            existing_roles = existing_user.get("roles", [])
            conflicting_roles = [role for role in request.roles if role in existing_roles]
            
            if conflicting_roles:
                raise HTTPException(
                    status_code=400,
                    detail=f"User already has registered as {conflicting_roles}"
                )

        # Remove previous verification attempts
        await verification_collection.delete_one({"_id": request.email})

        verification_code = str(random.randint(100000, 999999))

        # Store verification data
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

# ✅ Resend Code
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


@router.post("/verify-code", response_model=Token)
async def verify_code(
    email: str = Form(..., description="User email address"),
    code: str = Form(..., description="6-digit verification code")
):
    """
    Verify email code and complete registration
    """
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

        # Check if user exists and update roles
        existing_user = await users_collection.find_one({"email": email})
        roles_to_add = verification["roles"]
        
        if existing_user:
            # Add new roles that don't already exist
            existing_roles = existing_user.get("roles", [])
            new_roles = [role for role in roles_to_add if role not in existing_roles]
            
            if new_roles:
                await users_collection.update_one(
                    {"email": email},
                    {
                        "$addToSet": {"roles": {"$each": new_roles}},
                        "$set": {"password": verification["password"]}
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="User already has all requested roles."
                )
        else:
            # Create new user
            referral_id = await generate_unique_referral_id(verification["name"] or "User")
            user_data = {
                "_id": str(uuid.uuid4()),
                "userId": str(uuid.uuid4()),
                "name": verification["name"],
                "email": email,
                "contactnumber": verification["contactnumber"],
                "referralId": referral_id,
                "password": verification["password"],
                "roles": roles_to_add,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "email_verified": True
            }
            await users_collection.insert_one(user_data)

        # Clean up verification data
        await verification_collection.delete_one({"_id": email})

        # Fetch updated user
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=500, detail="User creation failed.")

        roles = user.get("roles", [])
        user_id = user.get("userId") or user.get("_id")

        # Generate tokens
        access_token = create_access_token(
            data={"sub": email, "roles": roles, "user_id": user_id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_SECONDS)
        )

        refresh_token = create_refresh_token(
            data={"sub": email, "roles": roles, "user_id": user_id},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
            roles=roles,
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during verification. Please try again."
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user.email, "roles": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "roles": user.roles},
        expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token, 
        refresh_token=refresh_token, 
        token_type="bearer", 
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS, 
        roles=user.roles
    )

@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    try:
        # Decode and validate refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Check if the user exists
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Generate new access and refresh tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": email, "role": user["role"]}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": email, "role": user["role"]}, expires_delta=refresh_token_expires
        )

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS, role=user["role"])

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

