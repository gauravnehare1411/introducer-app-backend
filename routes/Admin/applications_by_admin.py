from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.user_models import User
from config.database import applications_by_admin_collection
from schemas.user_auth import get_current_user
from schemas.gdrive_upload import get_drive_service, get_root_folder


router = APIRouter(prefix='/admin')

@router.get("/mortgage-applications")
async def get_user_mortgage_applications(current_user: User = Depends(get_current_user)):
    try:
        applications = await applications_by_admin_collection.find(
        ).sort("created_at", -1).to_list(length=100)
        
        for app in applications:
            app["_id"] = str(app["_id"])

        return applications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")


@router.delete("/mortgage-application/{application_id}")
async def delete_mortgage_application(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        application = await applications_by_admin_collection.find_one(
            {"_id": ObjectId(application_id)}
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        customer_id = application.get("customerId")
        drive_service = get_drive_service()

        try:
            root_folder_id = get_root_folder(drive_service)
            folder_list = drive_service.files().list(
                q=f"name='{customer_id}' and '{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name)"
            ).execute().get("files", [])

            if folder_list:
                folder_id = folder_list[0]["id"]
                drive_service.files().update(
                    fileId=folder_id,
                    body={"trashed": True}
                ).execute()
                print(f"🗑️ Moved customer folder '{customer_id}' (and its contents) to Trash.")
            else:
                print(f"⚠️ Folder '{customer_id}' not found in Drive.")

        except Exception as e:
            print(f"⚠️ Could not move folder '{customer_id}' to Trash: {e}")

        result = await applications_by_admin_collection.delete_one(
            {"_id": ObjectId(application_id)}
        )

        if result.deleted_count == 1:
            return {"message": "Application deleted successfully and folder moved to Trash."}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete application")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting application: {str(e)}")

