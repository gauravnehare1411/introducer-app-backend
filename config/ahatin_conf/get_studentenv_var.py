from dotenv import find_dotenv, load_dotenv
import os

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

AHATIN_MONGO_URL = os.getenv("AHATIN_MONGO_URL")
AHATIN_SECRET_KEY = os.getenv("AHATIN_SECRET_KEY")
AHATIN_ALGORITHM = os.getenv("AHATIN_ALGORITHM")

ahatin_email_address = os.getenv("ahatin_email_address")
ahatin_email_password = os.getenv("ahatin_email_password")