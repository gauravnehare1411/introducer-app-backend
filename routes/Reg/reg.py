from fastapi import APIRouter
from config.database import registrations
from reg_model import Registration

router = APIRouter()

@router.post("/api/register")
async def register_user(data: Registration):
    await registrations.insert_one(data.dict())
    return {"message": "Registration successful!"}