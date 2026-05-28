import os
from dotenv import load_dotenv

load_dotenv()   #   fetching variables from .env file

"""
.env format:

MODEL_PATH = ""
OUTPUT_DIR = ""
CSV_PATH = ""
CB_CSV_PATH = ""
SPAM_CSV_PATH = ""
TOXIC_CSV_PATH = ""
GROOMING_CSV_PATH = ""
"""

#   if none are present, set to none
MODEL_PATH =        os.getenv("MODEL_PATH", "./ai_research/model")
OUTPUT_DIR =        os.getenv("OUTPUT_DIR", "./ai_research/training_results")
CB_CSV_PATH =       os.getenv("CB_CSV_PATH", "./path/to/cyberbullying_dataset")
SPAM_CSV_PATH =     os.getenv("SPAM_CSV_PATH", "./path/to/spam_dataset")
TOXIC_CSV_PATH =    os.getenv("TOXIC_CSV_PATH", "./path/to/hate_dataset")
GROOMING_CSV_PATH =    os.getenv("TOXIC_CSV_PATH", "./path/to/grooming_dataset")