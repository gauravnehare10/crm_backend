import os 
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

MONGO_URL = os.getenv("MONGO_URL")

conn = MongoClient(MONGO_URL)

email_address = os.getenv("email_address")

email_password = os.getenv("email_password")