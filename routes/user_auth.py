import uuid
from fastapi import APIRouter, HTTPException
from models.user_models import Token, RegisterUser
from schemas.user_auth import *
from config.database import users_collection
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

router = APIRouter()

@router.post("/register", response_model=Token)
async def add_user(request: RegisterUser):
    try:
        request.username = request.username.lower()

        # Check for existing user by username
        if await users_collection.find_one({"username": request.username}):
            raise HTTPException(status_code=400, detail="Username already exists.")
        
        # Check for existing user by email
        if await users_collection.find_one({"email": request.email}):
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Hash the password
        hashed_password = hash_password(request.password)

        user_data = {
            "_id": str(uuid.uuid4()),
            "name": request.name,
            "username": request.username,
            "email": request.email,
            "contactnumber": request.contactnumber,
            "password": hashed_password,
        }

        # Insert user into the database
        await users_collection.insert_one(user_data)

        # Generate token for automatic login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": request.username}, expires_delta=access_token_expires
        )

        refresh_token = create_refresh_token(
            data={"sub": request.username}, expires_delta=refresh_token_expires
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
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS)


@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    try:
        # Decode and validate refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Check if the user exists
        user = await users_collection.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Generate new access and refresh tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": username}, expires_delta=refresh_token_expires
        )

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_SECONDS)

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

