from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from config.database import job_collection

router = APIRouter(tags=["Jobs"])

@router.put("/jobs/status")
def update_job_status(job_id: str, status: str):
    try:
        status = status.lower()

        valid_status = ["queued", "running", "completed"]

        if status not in valid_status:
            raise HTTPException(status_code=400, detail="Invalid status")

        obj_id = ObjectId(job_id)

        job = job_collection.find_one({"_id": obj_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        current_status = job.get("job_status", "").lower()

        if current_status == status:
            return {
                "message": f"Job is already in '{status}' state",
                "job_id": job_id
            }
        valid_transitions = {
            "queued": ["running"],
            "running": ["completed"],
            "completed": []
        }
        if status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{current_status}' to '{status}'"
            )

        update_data = {
            "job_status": status,
            "updated_at": datetime.utcnow()
        }

        if status == "running" and not job.get("started_at"):
            update_data["started_at"] = datetime.utcnow()
            
        if status == "completed" and not job.get("finished_at"):
            update_data["finished_at"] = datetime.utcnow()

        job_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        return {
            "message": "Job status updated successfully",
            "job_id": job_id,
            "previous_status": current_status,
            "new_status": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))