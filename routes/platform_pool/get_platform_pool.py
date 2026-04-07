from fastapi import APIRouter, Query
from bson import ObjectId
from bson.errors import InvalidId

from config.database import platform_pool_collection
from utils.response import success, failed

router = APIRouter(tags=["Platform Pool"])

def convert_objectid(data):
    if isinstance(data, dict):
        return {k: str(v) if isinstance(v, ObjectId) else convert_objectid(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_objectid(i) for i in data]
    return data
@router.get("/metrics/get")
def get_metrics(
    id: str = Query(default=None),
    ip_address: str = Query(default=None),
    os: str = Query(default=None),
    server_name: str = Query(default=None)
):
    try:
        query = {}
        if id:
            try:
                query["_id"] = ObjectId(id)
            except InvalidId:
                return failed("Invalid id provided", 400)

        if ip_address:
            query["ip_address"] = ip_address

        if os:
            query["os"] = os

        if server_name:
            query["server_name"] = server_name

        if query:
            data = list(platform_pool_collection.find(query))

            if not data:
                return failed("No matching data found", 404)

            return success(
                "Filtered data fetched successfully",
                convert_objectid(data)
            )

        all_data = list(platform_pool_collection.find())

        if not all_data:
            return success("No data available", [])

        return success(
            "All system metrics fetched successfully",
            convert_objectid(all_data)
        )

    except Exception as e:
        return failed(str(e), 500)