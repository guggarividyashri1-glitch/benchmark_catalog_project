from fastapi import APIRouter, Depends
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from config.database import catalog_collection
from utils.auth import user_or_admin
from utils.response import success, failed
from models.update_catalog_model import UpdateCatalog

router = APIRouter()
@router.patch("/catalog/update/{id}")
def update_catalog(id: str, payload: UpdateCatalog, user=Depends(user_or_admin)):

    try:
        obj_id = ObjectId(id)
    except InvalidId:
        return failed("Invalid catalog id", 400)

    catalog = catalog_collection.find_one({"_id": obj_id})

    if not catalog:
        return failed("Catalog not found", 404)

    payload_dict = payload.model_dump(exclude_unset=True)

    if not payload_dict:
        return failed("No fields provided for update", 400)

    changes = []
    update_fields = {}

    for key, value in payload_dict.items():

        old_value = catalog.get(key)

        if old_value != value:

            changes.append({
                "path": key,
                "old_value": old_value,
                "new_value": value
            })

            update_fields[key] = value

    if not changes:
        return failed("No changes detected", 400)

    current_version = int(catalog.get("catalog_version", 1))
    new_version = current_version + 1

    update_fields["catalog_version"] = str(new_version)

    history_entry = {
        "catalog_version": str(new_version),
        "changed_on": datetime.utcnow(),
        "changed_by": user.get("email", "unknown_user"),
        "change_type": "UPDATE",
        "summary": "Catalog updated",
        "changes": changes
    }

    catalog_collection.update_one(
        {"_id": obj_id},
        {
            "$set": update_fields,
            "$push": {"history": history_entry}
        }
    )

    return success("Catalog updated successfully")