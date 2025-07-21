import uuid
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from models.user_models import Token, RegisterUser, EmailOnlyRequest
from schemas.user_auth import *
from config.database import users_collection, verification_collection
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

router = APIRouter()


@router.post("/register")
async def start_registration(request: RegisterUser, background_tasks: BackgroundTasks):
    try:
        request.email = request.email.lower()

        # Check if user is already registered
        if await users_collection.find_one({"email": request.email}):
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Always remove previous verification attempt (if any)
        await verification_collection.delete_one({"_id": request.email})

        verification_code = str(random.randint(100000, 999999))

        # Insert new verification record (with 5-minute expiry)
        await verification_collection.insert_one({
            "_id": request.email,
            "name": request.name,
            "contactnumber": request.contactnumber,
            "password": hash_password(request.password),
            "code": verification_code,
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        })

        background_tasks.add_task(send_verification_email, request.email, verification_code)

        return {"message": "A new verification code has been sent to your email."}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

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
            {
                "$set": {
                    "code": new_code,
                    "expires_at": datetime.utcnow() + timedelta(minutes=5)
                }
            }
        )

        background_tasks.add_task(send_verification_email, request.email, new_code)
        return {"message": "A new verification code has been sent to your email."}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/verify-code", response_model=Token)
async def verify_code(email: str = Form(...), code: str = Form(...)):
    try:
        email = email.lower()
        verification = await verification_collection.find_one({"_id": email})

        if not verification or verification["code"] != code:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
        
        # Check if code is expired
        if verification["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

        # Generate referral ID
        referral_id = await generate_unique_referral_id(verification["name"] or "XX")

        user_data = {
            "_id": str(uuid.uuid4()),
            "name": verification["name"],
            "email": email,
            "contactnumber": verification["contactnumber"],
            "referralId": referral_id,
            "password": verification["password"],
        }

        await users_collection.insert_one(user_data)
        await verification_collection.delete_one({"_id": email})

        # Generate tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )

        refresh_token = create_refresh_token(
            data={"sub": email}, expires_delta=refresh_token_expires
        )

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


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
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS)


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
            data={"sub": email}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": email}, expires_delta=refresh_token_expires
        )

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS)

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

