from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "benchmark_db")
COLLECTION_NAME = os.getenv("COLLECTION", "benchmark_catalog")

try:
    client = MongoClient(MONGO_URL)

    # Force actual connection check
    client.admin.command("ping")

    db = client[DB_NAME]

    catalog_collection = db[COLLECTION_NAME]
    benchmark_execution_collection = db["benchmark_execution"]
    workflow_runs_collection = db["workflow_runs"]
    workflow_catalog_collection = db["workflow_catalog"]
    platform_pool_collection = db["platform_pool"]
    job_collection=db["jobs"]
    benchmark_collection = db["benchmark_results"]
    sme_mapping_collection = db["sme_mapping"]

    print(f"MongoDB connected successfully: {MONGO_URL}, DB: {DB_NAME}")

except ServerSelectionTimeoutError:
    raise Exception("MongoDB not reachable. Check if MongoDB is running or URL is incorrect.")

except Exception as e:
    raise Exception(f"MongoDB connection failed: {str(e)}")