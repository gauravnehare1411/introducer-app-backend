from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import users_collection, referrals_collection
from models.referral_models import StatusUpdate

router = APIRouter(prefix="/admin")

# Helper function to convert ObjectId to str
def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/users")
async def get_all_users():
    users_cursor = users_collection.find({})
    users = [fix_id(user) async for user in users_cursor]
    return users


@router.get("/referrals/{referral_id}")
async def get_referrals_by_referral_id(referral_id: str):
    referrals_cursor = referrals_collection.find({"referralId": referral_id})
    referrals = [fix_id(ref) async for ref in referrals_cursor]
    return referrals


@router.patch("/referrals/{referral_id}/status")
async def update_referral_status(referral_id: str, update: StatusUpdate):
    result = await referrals_collection.update_one(
        {"_id": referral_id},
        {"$set": {"status": update.status}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Referral not found or already up to date")

    return {"message": "Referral status updated successfully"}