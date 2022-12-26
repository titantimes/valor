import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
