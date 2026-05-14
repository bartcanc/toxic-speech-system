import os
from dotenv import load_dotenv

load_dotenv()   #   fetching variables from .env file

"""
.env format:

SECRET_KEY=""
DATABASE_URL=""
DATABASE_PATH=""
MODEL_PATH=""

"""

#   if none are present, set to none
SECRET_KEY = os.getenv("SECRET_KEY", "none")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend_api/databases/database.db")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./backend_api/databases")
MODEL_PATH = os.getenv("MODEL_PATH", "./ai_research/model")