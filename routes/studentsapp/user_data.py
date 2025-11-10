from fastapi import APIRouter, Depends
from typing import Annotated
from models.students_models.auth_models import User
from schemas.student_auth.auth_schema import get_current_user

router = APIRouter()

@router.get('/user', response_model=User)
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user