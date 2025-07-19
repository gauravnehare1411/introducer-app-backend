from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import  user_auth, mortgage

app = FastAPI()

app.include_router(user_auth.router)
app.include_router(mortgage.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)