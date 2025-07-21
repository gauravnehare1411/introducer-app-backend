from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import find_dotenv, load_dotenv
import os

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

MONGO_URL = os.getenv("MONGO_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.mortgage

users_collection = db.users_collection
referrals_collection = db.referrals_collection
verification_collection = db.verification_collection

