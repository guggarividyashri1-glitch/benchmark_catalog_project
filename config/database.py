from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "benchmark_db")
COLLECTION_NAME = os.getenv("COLLECTION", "benchmark_catalog")

try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    catalog_collection = db[COLLECTION_NAME]
    print(f"Connected to MongoDB: {MONGO_URL}, DB: {DB_NAME}, Collection: {COLLECTION_NAME}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise e