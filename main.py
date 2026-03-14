from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import  user_auth, referrals, user_details, mortgage_applications
from routes.Admin import admin, applications_by_admin, applications_by_user, aws_save_and_upload
from routes.AAIFinFactFind import mortgage_data

app = FastAPI()

app.include_router(user_auth.router)
app.include_router(referrals.router)
app.include_router(admin.router)
app.include_router(user_details.router)
app.include_router(mortgage_applications.router)
app.include_router(applications_by_admin.router)
app.include_router(applications_by_user.router)
app.include_router(aws_save_and_upload.router)
app.include_router(mortgage_data.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)