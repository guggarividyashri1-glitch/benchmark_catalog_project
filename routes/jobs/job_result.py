from fastapi import APIRouter, Header
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from config.database import job_collection
from models.job_result_model import JobResultModel
from utils.response import success, failed  

router = APIRouter(tags=["Jobs"])
@router.post("/jobs/result")
def update_job_result(payload: JobResultModel, job_id: str = Header(...)):
    try:
        try:
            obj_id = ObjectId(job_id)
        except InvalidId:
            return failed("Invalid job id", 400)

        job = job_collection.find_one({"_id": obj_id})
        if not job:
            return failed("Invalid job id", 404)

        current_status = job.get("job_status", "")

        success_values = []
        formatted_result = []

        for item in payload.result:

            if len(item) != 1:
                return failed("Result not updated in database", 400)

            temp = {}

            for sut_id, details in item.items():

                if not sut_id or not str(sut_id).strip():
                    return failed("sut_id is compulsory", 400)

                if details.success is None:
                    return failed("success is compulsory", 400)

                success_values.append(details.success)

                temp[sut_id] = details.dict()

            formatted_result.append(temp)

        valid = False

        if current_status == "completed":
            valid = all(success_values)

        elif current_status == "running":
            valid = (any(success_values) and not all(success_values))

        else:
            valid = False

        if not valid:
            return failed("Result not updated in database", 400)

        res = job_collection.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "result": formatted_result,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if res.matched_count == 1:
            return success("Result updated successfully", formatted_result, 200)
        else:
            return failed("Result not updated in database", 500)

    except Exception:
        return failed("Result not updated in database", 500)