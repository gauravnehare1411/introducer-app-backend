from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from models.form_models import MortgageDetails
from config.database import users_collection
from schemas.user_auth import get_current_user
from models.user_models import User

router = APIRouter()

@router.post("/add_mortgage_data/")
async def add_mortgage_data(data: MortgageDetails, current_user: User=Depends(get_current_user)):
    try:
        user_doc = await users_collection.find_one({"username": current_user.userId})
        
        if data.hasMortgage:
            entry = {
                "_id": ObjectId(),
                "hasMortgage": data.hasMortgage,
                "paymentMethod": data.paymentMethod,
                "estPropertyValue": data.estPropertyValue,
                "mortgageAmount": data.mortgageAmount,
                "loanToValue1": data.loanToValue1,
                "furtherAdvance": data.furtherAdvance,
                "mortgageType": data.mortgageType,
                "productRateType": data.productRateType,
                "renewalDate": data.renewalDate,
                'reference1': data.reference1,
            }
            # Append to mortgage_details array
            await users_collection.update_one(
                {"username": data.username},
                {"$push": {"mortgage_details": entry}}
            )
        else:
            entry = {
                "_id": ObjectId(),
                "isLookingForMortgage": data.isLookingForMortgage,
                "foundProperty": data.foundProperty,
                "newMortgageType": data.newMortgageType,
                "depositAmount": data.depositAmount,
                "purchasePrice": data.purchasePrice,
                "loanToValue2": data.loanToValue2,
                "loanAmount": data.loanAmount,
                "sourceOfDeposit": data.sourceOfDeposit,
                "loanTerm": data.loanTerm,
                "newPaymentMethod": data.newPaymentMethod,
                'reference2': data.reference2
            }
            # Append to new_mortgage_requests array
            await users_collection.update_one(
                {"UserId": current_user.userId},
                {"$push": {"new_mortgage_requests": entry}}
            )
        
        return {"message": "Data added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))