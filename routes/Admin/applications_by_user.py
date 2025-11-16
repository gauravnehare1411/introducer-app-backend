from fastapi import APIRouter, Depends, HTTPException
from models.user_models import User
from schemas.user_auth import requires_roles
from config.database import mortgage_applications_collection

router = APIRouter(prefix='/admin')

@router.get('/all-applications-by-user')
async def get_all_applications_by_users(current_user: User=Depends(requires_roles(['admin']))):
    try:
        applications = await mortgage_applications_collection.find(
        ).sort("created_at", -1).to_list(length=100)
        
        for app in applications:
            app["_id"] = str(app["_id"])

        return applications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")
    
