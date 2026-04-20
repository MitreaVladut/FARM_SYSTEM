# check_db.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

print(f"Collections found: {db.list_collection_names()}")
print(f"Inventory count: {db.inventory.count_documents({})}")