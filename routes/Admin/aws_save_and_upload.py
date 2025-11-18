from fastapi import APIRouter, Request, Depends, UploadFile, HTTPException, Form, File
from models.user_models import User
from schemas.user_auth import get_current_user
from schemas.aws_upload_schema import upload_to_s3_async, generate_presigned_url, delete_customer_folder_s3, delete_from_s3_async
from config.database import applications_by_admin_collection
from datetime import datetime
from bson import ObjectId
import json
from typing import List

router = APIRouter()

@router.post("/submit_mortgage_with_docs")
async def submit_mortgage_with_docs(
    request: Request,
    id_proof: UploadFile | None = None,
    address_proof: UploadFile | None = None,
    bank_statement: UploadFile | None = None,
    payslip: UploadFile | None = None,
    current_user: User = Depends(get_current_user),
):
    try:
        form_data = await request.form()
        form_dict = dict(form_data)

        # Extract customerId from frontend
        customerId = form_dict.get("customerId")
        if not customerId:
            raise HTTPException(status_code=400, detail="customerId missing")

        # Upload files to S3
        uploaded_files = {}
        for key, file in {"id_proof": id_proof, "address_proof": address_proof,
                          "bank_statement": bank_statement, "payslip": payslip}.items():
            if file:
                s3_key = await upload_to_s3_async(file, folder=f"{customerId}/{key}")
                uploaded_files[key] = {
                    "file_name": file.filename,
                    "s3_key": s3_key
                }

        # Separate top-level fields vs form fields
        top_level_data = {
            "customerId": customerId,
            "submitted_by": current_user.email,
            "uploaded_files": uploaded_files,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "submitted"
        }

        # Remove top-level fields from form_data
        form_fields = {
            k: v for k, v in form_dict.items()
            if k not in ["customerId", "id_proof", "address_proof", "bank_statement", "payslip"]
        }

        # Final document
        final_document = {**top_level_data, "form_data": form_fields}


        # Save to MongoDB
        result = await applications_by_admin_collection.insert_one(final_document)

        return {
            "message": "Mortgage application submitted successfully",
            "application_id": str(result.inserted_id),
            "customerId": customerId,
            "uploaded_files": uploaded_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting application: {str(e)}")
    
    
@router.get("/get_file")
async def get_file(customerId: str, file_key: str, current_user: User = Depends(get_current_user)):
    try:
        url = await generate_presigned_url(file_key)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate URL: {str(e)}")
    

@router.delete("/delete-mortgage-application/{application_id}")
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

        # Delete all S3 files for this customer
        try:
            await delete_customer_folder_s3(customer_id)
        except Exception:
            # Do not block deletion if S3 cleanup fails
            pass

        result = await applications_by_admin_collection.delete_one(
            {"_id": ObjectId(application_id)}
        )

        if result.deleted_count != 1:
            raise HTTPException(status_code=500, detail="Failed to delete application")

        return {
            "message": "Application deleted successfully along with associated S3 files."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting application: {str(e)}"
        )
    

@router.put("/update-mortgage-with-docs/{application_id}")
async def update_mortgage_with_docs(
    application_id: str,
    form_data: str = Form(...),
    files: List[UploadFile] = File([]),
    file_keys: List[str] = Form([]),
    current_user: User = Depends(get_current_user)
):
    try:
        data = json.loads(form_data)

        await applications_by_admin_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"form_data": data, "updated_at": datetime.utcnow()}}
        )

        if files:
            app_doc = await applications_by_admin_collection.find_one(
                {"_id": ObjectId(application_id)}
            )
            customer_id = app_doc["customerId"]
            uploaded_files = app_doc.get("uploaded_files", {})

            for file, key in zip(files, file_keys):

                old_file = uploaded_files.get(key)
                if old_file and "s3_key" in old_file:
                    await delete_from_s3_async(old_file["s3_key"])

                new_s3_key = await upload_to_s3_async(
                    file,
                    folder=f"{customer_id}/{key}"
                )

                uploaded_files[key] = {
                    "file_name": file.filename,
                    "s3_key": new_s3_key
                }

            await applications_by_admin_collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"uploaded_files": uploaded_files}}
            )

        return {
            "status": "success",
            "message": "Application updated successfully."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))