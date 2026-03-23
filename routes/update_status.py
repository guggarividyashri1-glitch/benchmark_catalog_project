from fastapi import APIRouter, Depends
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from config.database import catalog_collection
from utils.auth import verify_token
from utils.response import success, failed

router = APIRouter()

STATUS_MAP = {
    "draft": "DRAFT",
    "pending-approval": "PENDING-APPROVAL",
    "approved": "APPROVED",
    "rejected": "REJECTED",
    "published": "PUBLISHED"
}
@router.patch("/catalog/status/{id}")
def update_status(id: str, new_status: str, user=Depends(verify_token)):

    normalized_status = STATUS_MAP.get(new_status.lower())
    if not normalized_status:
        return failed(f"Invalid status '{new_status}' provided", 400)

    try:
        catalog_id = ObjectId(id)
    except InvalidId:
        return failed("Invalid catalog id", 400)

    catalog = catalog_collection.find_one({"_id": catalog_id})
    if not catalog:
        return failed("Catalog not found", 404)

    current_status = catalog.get("status", "DRAFT")
    role = user.get("role")

    if current_status == normalized_status:
        return failed(f"Status already set to {normalized_status}", 400)

    user_transitions = {
        "DRAFT": ["PENDING-APPROVAL"]
    }

    admin_transitions = {
        "DRAFT": ["PENDING-APPROVAL"],
        "PENDING-APPROVAL": ["APPROVED", "REJECTED"],
        "APPROVED": ["PUBLISHED"]
    }

    if role == "user":
        if current_status not in user_transitions:
            return failed(f"User is not allowed to update from {current_status}", 403)

        if normalized_status not in user_transitions[current_status]:
            return failed("User is not allowed to perform this status change", 403)

    elif role == "admin":
        if current_status not in admin_transitions:
            return failed(f"Admin cannot update from {current_status}", 400)

        if normalized_status not in admin_transitions[current_status]:
            return failed(
                f"Invalid transition from {current_status} to {normalized_status}",
                400
            )

    else:
        return failed("Unauthorized role", 403)

    catalog_collection.update_one(
        {"_id": catalog_id},
        {
            "$set": {"status": normalized_status},
            "$push": {
                "history": {
                    "catalog_version": catalog.get("catalog_version", "1"),
                    "changed_on": datetime.utcnow(),
                    "changed_by": user.get("email", role),
                    "change_type": "UPDATE",
                    "summary": f"Status changed from {current_status} to {normalized_status}",
                    "changes": [
                        {
                            "path": "status",
                            "old_value": current_status,
                            "new_value": normalized_status
                        }
                    ]
                }
            }
        }
    )

    return success(f"Catalog status updated to {normalized_status}")