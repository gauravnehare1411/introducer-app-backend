from fastapi import APIRouter, HTTPException, Depends, Query, status as http_status, Path
from bson import ObjectId
from config.ahatin_conf.students_db import users_collection, applications_collection, deleted_users_collection
from models.students_models.form_models import StatusUpdate, ApplicationForm
from schemas.student_auth.auth_schema import requires_roles
from datetime import datetime
from typing import Optional
from fastapi.responses import JSONResponse


router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(requires_roles(["admin"]))]
    )

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/students/")
async def get_all_students():
    users = await users_collection.find({'roles': 'student'}).to_list(length=None)
    return [fix_id(user) for user in users]

@router.put("/student/{user_id}")
async def update_user(user_id: str, body: dict):
    name = body.get("name")
    contactnumber = body.get("contactnumber")

    updates = {}
    if isinstance(name, str):
        updates["name"] = name.strip()
    if isinstance(contactnumber, str):
        updates["contactnumber"] = contactnumber.strip()

    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided.")

    result = await users_collection.update_one({"userId": user_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    user = await users_collection.find_one({"userId": user_id}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return fix_id(user)


@router.delete("/student/{user_id}")
async def delete_user(user_id: str):
    user = await users_collection.find_one({"userId": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["deletedAt"] = datetime.utcnow()
    await deleted_users_collection.insert_one(user)

    result = await users_collection.delete_one({"userId": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete user")

    return {"message": "User deleted and moved to deleted_users collection"}


@router.get("/student/applications/{userId}")
async def get_student_applications(userId: str):
    if not userId:
        raise HTTPException(status_code=401, detail='User not found or authorized')
    
    applications = await applications_collection.find({"userId": userId}).to_list(length=None)
    if not applications:
        raise HTTPException(status_code=404, detail="User not found.")
    
    for doc in applications:
        doc["_id"] = str(doc["_id"])
    
    return applications


@router.put("/application/{application_id}/status")
async def update_application_status(application_id: str, payload: dict):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status field is required.")

    try:
        result = await applications_collection.update_one(
            {"applicationId": application_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Application not found.")
        updated_app = await applications_collection.find_one({"applicationId": application_id})

        return JSONResponse(content=updated_app['applicationId'], status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/application/{application_id}/edit")
async def update_application(
    application_id: str = Path(...),
    application: ApplicationForm = None
):
    existing = await applications_collection.find_one({"applicationId": application_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Application not found")
    
    updated_data = application.dict()
    updated_data["updated_at"] = datetime.utcnow().isoformat()

    await applications_collection.update_one(
        {"applicationId": application_id},
        {"$set": updated_data}
    )

    return {"message": "Application updated successfully"}