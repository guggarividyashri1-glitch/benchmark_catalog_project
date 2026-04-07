from fastapi import APIRouter, Depends
from config.database import catalog_collection
from utils.auth import user_or_admin
from utils.response import success, failed
from bson import ObjectId

router = APIRouter()
@router.get("/catalog/getall")
def get_catalog(id: str = None, user=Depends(user_or_admin)):

    pipeline = []
    if id:
        try:
            pipeline.append({
                "$match": {
                    "_id": ObjectId(id),
                    "deleted_flag": False
                }
            })
        except:
            return failed("Enter valid id")

    else:
        pipeline.append({
            "$match": {
                "deleted_flag": False
            }
        })

    pipeline.append(
        {
            "$project": {
                "catalog_name": 1,
                "benchmark_name": 1,
                "benchmark_category": 1
            }
        }
    )

    data = list(catalog_collection.aggregate(pipeline))

    if not data:
        return failed("Catalog not found")

    for d in data:
        d["_id"] = str(d["_id"])

    return success("Catalog fetched successfully", data)