from fastapi import APIRouter, HTTPException, Depends
from models.mortgage_models import FormData
from models.user_models import User
from schemas.user_auth import requires_roles
from config.database import  mortgage_form

router = APIRouter(prefix="/mortgage")

@router.post("/save-form-data")
async def save_form_data(form_data: FormData, current_user: User=Depends(requires_roles(['admin']))):
    try:
        await mortgage_form.update_one(
            {
                "formName": form_data.formName,
                "UserId": current_user.userId
            },
            {"$set": {"data": form_data.data}},
            upsert=True,
        )

        return {"message": "Form data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-form-data/{form_name}")
async def get_form_data(form_name: str, current_user: User=Depends(requires_roles(['admin']))):
    try:
        result = await mortgage_form.find_one({"formName": form_name, "UserId": current_user.userId}, {"_id": 0})
        if result:
            return result["data"]
        else:
            return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
