from fastapi import APIRouter, Depends
from config.database import catalog_collection
from utils.auth import admin_only
from utils.response import success, failed
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()
@router.delete("/catalog/delete/{id}")
def delete_catalog(id: str, user=Depends(admin_only)):
    try:
        catalog_id = ObjectId(id)
    except InvalidId:
        return failed("Enter valid catalog id", 400)

    catalog = catalog_collection.find_one({"_id": catalog_id})

    if not catalog:
        return failed("Catalog not found", 404)

    if catalog["status"] not in ["DRAFT", "PENDING-APPROVAL", "REJECTED"]:
        return failed("Catalog cannot be deleted", 400)

    catalog_collection.update_one(
        {"_id": catalog_id},
        {
            "$set": {
                "deleted_flag": True,
                "status": "ARCHIVED"
            }
        }
    )

    return success("Catalog archived successfully")