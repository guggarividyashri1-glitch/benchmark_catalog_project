from fastapi import APIRouter, Query
from bson import ObjectId
from bson.errors import InvalidId

from config.database import job_collection
from utils.response import success, failed

router = APIRouter(tags=["Jobs"])
@router.get("/jobs/get")
def get_jobs(
    job_id: str = Query(default=None),
    job_status: str = Query(default=None)
):
    try:
        query = {}
        if job_id:
            query["_id"] = ObjectId(job_id)
        if job_status:
            query["job_status"] = job_status.lower()

        jobs = list(job_collection.find(query))

        if not jobs:
            return failed("No jobs found", 404)

        result = []
        for i, job in enumerate(jobs, start=1):
            result.append({
                "job_number": i,
                "job_id": str(job["_id"]),
                "job_status": job.get("job_status"),
                "result": job.get("result", [])   
            })
        return success("Jobs fetched successfully", result)

    except InvalidId:
        return failed("Invalid job id provided", 400)

    except Exception as e:
        return failed(str(e), 500)