from fastapi import APIRouter, Depends, HTTPException
from routes.user_auth import get_current_user
from models.user_models import UserInDB
from datetime import datetime
from config.database import mortgage_applications_collection
from bson import ObjectId

router = APIRouter()


@router.post("/add_mortgage_data")
async def add_mortgage_data(
    mortgage_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        application_data = {
            **mortgage_data,
            "user_id": current_user.userId or current_user.id,
            "user_email": current_user.email,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "submitted"
        }
        
        result = await mortgage_applications_collection.insert_one(application_data)
        
        return {
            "message": "Mortgage application submitted successfully",
            "application_id": str(result.inserted_id),
            "user_id": current_user.userId
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting application: {str(e)}")
    

@router.get("/user/mortgage-applications")
async def get_user_mortgage_applications(current_user: UserInDB = Depends(get_current_user)):
    try:
        applications = await mortgage_applications_collection.find(
            {"user_email": current_user.email}
        ).sort("created_at", -1).to_list(length=100)
        
        # Convert ObjectId to string for JSON serialization
        for app in applications:
            app["_id"] = str(app["_id"])
        
        return applications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")


@router.delete("/user/mortgage-application/{application_id}")
async def delete_mortgage_application(
    application_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        # Verify user owns this application
        application = await mortgage_applications_collection.find_one(
            {"_id": ObjectId(application_id), "user_email": current_user.email}
        )
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        result = await mortgage_applications_collection.delete_one(
            {"_id": ObjectId(application_id)}
        )
        
        if result.deleted_count == 1:
            return {"message": "Application deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete application")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting application: {str(e)}")


@router.put("/user/mortgage-application/{application_id}")
async def update_mortgage_application(
    application_id: str,
    update_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        application = await mortgage_applications_collection.find_one(
            {"_id": ObjectId(application_id), "user_email": current_user.email}
        )
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        update_data["updated_at"] = datetime.utcnow()
        
        await mortgage_applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": update_data}
        )
        
        return {"message": "Application updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating application: {str(e)}")