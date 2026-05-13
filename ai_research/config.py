import os
from dotenv import load_dotenv

load_dotenv()   #   fetching variables from .env file

#   if none are present, set to none
MODEL_PATH = os.getenv("MODEL_PATH", "./ai_research/model")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./ai_research/training_results")
CSV_PATH = os.getenv("CSV_PATH", "./ai_research/dane/pan12_dataset.csv")