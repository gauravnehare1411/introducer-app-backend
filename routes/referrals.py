from fastapi import APIRouter, Depends, HTTPException, status
from models.user_models import User
from models.referral_models import ReferralCreate
from config.database import referrals_collection
from uuid import uuid4
from schemas.user_auth import get_current_user

router = APIRouter()

@router.post("/submit-referral")
async def submit_referral(referral: ReferralCreate, current_user: User = Depends(get_current_user)):
    try:
        referral_data = referral.dict()
        print(referral_data)
        referral_data.update({
            "_id": str(uuid4()),
            "referralId": current_user.referralId,
            "status": "pending"
        })
        print(referral_data)
        await referrals_collection.insert_one(referral_data)
        return {"message": "Referral submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/my-referrals")
async def get_my_referrals(current_user: User = Depends(get_current_user)):
    try:
        referrals = await referrals_collection.find({"referralId": current_user.referralId}).to_list(length=None)
        return referrals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching referrals: {str(e)}")