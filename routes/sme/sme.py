from fastapi import APIRouter, Body
from datetime import datetime
import traceback
from config.database import sme_mapping_collection
from utils.response import success, failed

router = APIRouter(prefix="/sme", tags=["sme"])
def get_sme_email():
    return "guggarividyashri1@gmail.com"
def classify_level(payload: dict):
    required_fields = [
        "benchmark_name",
        "environment",
        "metric_name",
        "metric_value"
    ]

    allowed_benchmarks = ["nginx", "redis", "speccpv"]

    if payload.get("benchmark_name") not in allowed_benchmarks:
        return None, "Invalid benchmark_name"

    missing_fields = [
        field for field in required_fields
        if payload.get(field) in [None, ""]
    ]

    if missing_fields:
        return {"level": "L1"}, None

    return {"level": "L2"}, None


@router.post("/create-sme-mapping")
def create_sme_mapping(payload: dict = Body(...)):
    try:
        result_data, error = classify_level(payload)

        if error:
            return failed(error, 400)

        metrics = [payload]

        document = {
            "benchmark_name": payload.get("benchmark_name"),
            "metrics": metrics,
            "sme_mail_id": get_sme_email(),
            "level": result_data["level"],
            "created_at": datetime.utcnow()
        }

        result = sme_mapping_collection.insert_one(document)

        return success(
            "SME mapping created successfully",
            {
                "sme_mapping_id": str(result.inserted_id),
                "benchmark_name": payload.get("benchmark_name"),
                "level": result_data["level"]
            },
            201
        )

    except Exception as e:
        print(traceback.format_exc())
        return failed(str(e), 500)