from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from config.database import job_collection

router = APIRouter(tags=["Jobs"])
@router.put("/jobs/status")
def update_job_status(job_id: str, status: str):
    try:
        status = status.lower()

        valid_status = ["queued", "running", "completed", "failed"]
        if status not in valid_status:
            raise HTTPException(status_code=400, detail="Invalid status")

        try:
            obj_id = ObjectId(job_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid job id")

        job = job_collection.find_one({"_id": obj_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        current_status = job.get("job_status", "")

        if current_status == status:
            return {
                "message": f"Job is already in '{status}' state",
                "job_id": job_id
            }

        valid_transitions = {
            "queued": ["running"],
            "running": ["completed", "failed"],
            "completed": [],
            "failed": []
        }

        if status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{current_status}' to '{status}'"
            )

        success_flag = True if status == "completed" else False
        result_data = [
            {
                "0.0.0.0": {
                    "success": success_flag,
                    "message": "string",
                    "error": ""
                }
            },
            {
                "1.1.1.1": {
                    "success": success_flag,
                    "message": "",
                    "error": ""
                }
            }
        ]
        for item in result_data:
            for ip, val in item.items():
                if status in ["running", "failed"]:
                    val["success"] = True if ip == "0.0.0.0" else False
                elif status == "completed":
                    val["success"] = True

        update_fields = {
            "job_status": status,
            "updated_at": datetime.utcnow(),
            "result": result_data
        }

        if status == "running" and not job.get("started_at"):
            update_fields["started_at"] = datetime.utcnow()

        if status in ["completed", "failed"] and not job.get("finished_at"):
            update_fields["finished_at"] = datetime.utcnow()

        res = job_collection.update_one(
            {"_id": obj_id},
            {"$set": update_fields}
        )

        if res.matched_count == 0:
            raise HTTPException(status_code=500, detail="Update failed")

        return {
            "message": "Job status updated successfully",
            "job_id": job_id,
            "previous_status": current_status,
            "new_status": status
        }

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid job id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))