from fastapi import APIRouter, HTTPException, Depends, status
from models.students_models.form_models import ApplicationForm
from models.students_models.auth_models import User
from config.ahatin_conf.students_db import applications_collection, deleted_applications_collection
from schemas.student_auth.auth_schema import get_current_user
import uuid
from datetime import timezone, timedelta, datetime

IST = timezone(timedelta(hours=5, minutes=30))

router = APIRouter()

@router.post('/submit-application')
async def submit_application(data: ApplicationForm, current_user: User=Depends(get_current_user)):
    try:
        form_dict = data.dict()
        form_dict["applicationId"] = str(uuid.uuid4())
        form_dict["userId"] = current_user.userId
        form_dict["status"] = "Submitted"
        form_dict["updatedAt"] = datetime.now(IST).isoformat()
        form_dict["submitted_at"] = datetime.now(IST).isoformat()

        result = await applications_collection.insert_one(form_dict)
        return {"message": "Application saved successfully", "id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save application")
    
@router.get('/student/applications')
async def get_student_applications(current_user: User=Depends(get_current_user)):
    try:
        applications = await applications_collection.find({"userId": current_user.userId}).to_list(length=None)
        for app in applications:
                app["_id"] = str(app["_id"])

        return applications
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")
    

@router.get('/applications/{application_id}')
async def get_application_with_id(application_id: str, current_user: User=Depends(get_current_user)):
     try:
        application = await applications_collection.find_one({'applicationId': application_id})
        application['_id'] = str(application["_id"])
        return application
     except:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

@router.delete('/applications/{application_id}')
async def delete_application(application_id: str, current_user: User = Depends(get_current_user)):
    application = await applications_collection.find_one({'applicationId': application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application['deletedAt'] = datetime.utcnow()
    await deleted_applications_collection.insert_one(application)
    
    result = await applications_collection.delete_one({'applicationId': application_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete application")
    
    return {"message": "Application deleted and moved to deleted_applications collection"}
     