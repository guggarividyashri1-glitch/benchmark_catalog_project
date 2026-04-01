from fastapi import APIRouter
from datetime import datetime

from models.system_metrics_model import SystemMetrics
from config.database import system_metrics_collection
from utils.response import success, failed

router = APIRouter(tags=["Platform Pool"])
@router.post("/metrics/insert")
def insert_metrics(payload: SystemMetrics):

    try:
        data = payload.model_dump()
        data["ip_address"] = str(data["ip_address"])

        existing = system_metrics_collection.find_one({
            "ip_address": data["ip_address"]
        })

        if existing:
            return failed("Data already present for this IP address", 400)

        data["status"] = "active"
        data["created_on"] = datetime.utcnow()
        result = system_metrics_collection.insert_one(data)

        inserted_data = system_metrics_collection.find_one({
            "_id": result.inserted_id
        })

        inserted_data["_id"] = str(inserted_data["_id"])

        return success(
            "Platform pool inserted successfully",
            inserted_data
        )

    except Exception as e:
        return failed(f"Insertion failed: {str(e)}", 500)