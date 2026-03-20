import os
from dotenv import load_dotenv

load_dotenv()   #   fetching variables from .env file

#   if none are present, set to none
SECRET_KEY = os.getenv("SECRET_KEY", "none")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend_api/databases/toxic_logs.db")