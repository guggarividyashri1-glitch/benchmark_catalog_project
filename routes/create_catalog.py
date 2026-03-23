from fastapi import APIRouter, Depends
from config.database import catalog_collection
from models.catalog_model import Catalog
from utils.response import success, failed
from utils.auth import user_or_admin
from datetime import datetime

router = APIRouter()
@router.post("/catalog/create")
def create_catalog(data: Catalog, user=Depends(user_or_admin)):

    payload = data.model_dump()

    payload["name"] = payload["catalog_name"] + "_" + str(int(datetime.utcnow().timestamp()))

    payload["status"] = "DRAFT"

    payload["deleted_flag"] = False

    payload["owner"] = user["role"]

    result = catalog_collection.insert_one(payload)

    payload["_id"] = str(result.inserted_id)

    return success("Catalog created successfully", [payload], 201)