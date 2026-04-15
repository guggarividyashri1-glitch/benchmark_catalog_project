from fastapi import APIRouter, Query
from bson import ObjectId
from bson.errors import InvalidId

from config.database import (
    benchmark_execution_collection,
    workflow_runs_collection,
    workflow_catalog_collection,
    job_collection
)
from utils.response import success, failed

router = APIRouter(tags=["Benchmark Execution"])
def convert_objectid(data):
    if isinstance(data, dict):
        return {k: convert_objectid(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid(i) for i in data]
    elif isinstance(data, ObjectId):
        return str(data)
    return data
def get_jobs(be_id=None, wr_id=None, job_status=None):
    query = {}

    if be_id:
        query["benchmark_execution_id"] = str(be_id)

    if wr_id:
        query["workflow_run_id"] = str(wr_id)

    if job_status:
        query["job_status"] = job_status

    jobs = list(job_collection.find(query))
    return convert_objectid(jobs)

def build_response(be_doc, job_status=None):
    doc = convert_objectid(be_doc)

    wr = None
    if doc.get("workflow_runs_id"):
        wr = workflow_runs_collection.find_one(
            {"_id": ObjectId(doc["workflow_runs_id"])}
        )

    wr_id = doc.get("workflow_runs_id")

    jobs = get_jobs(be_id=doc["_id"], wr_id=wr_id, job_status=job_status)

    doc["jobs"] = jobs

    if wr:
        doc["workflow"] = convert_objectid(wr.get("workflow"))

    return doc

def match_search(doc, search):
    search = search.lower()
    def check(value):
        if isinstance(value, str):
            return search in value.lower()
        if isinstance(value, dict):
            return any(check(v) for v in value.values())
        if isinstance(value, list):
            return any(check(v) for v in value)
        return False

    return check(doc)
@router.get("/benchmark/get")
def get_benchmark(
    id: str = Query(default=None),
    job_status: str = Query(default=None),
    search: str = Query(default=None)  
):
    try:
        if id:
            obj_id = ObjectId(id)

            be = benchmark_execution_collection.find_one({"_id": obj_id})

            wr = (
                (not be and workflow_runs_collection.find_one({"_id": obj_id}))
                or None
            )

            if not be and wr:
                be = benchmark_execution_collection.find_one(
                    {"_id": ObjectId(wr["benchmark_execution_id"])}
                )

            wc = (
                (not be and not wr and
                 workflow_catalog_collection.find_one({"_id": obj_id}))
                or None
            )

            if wc:
                workflow_name = wc.get("workflow_data", {}).get("workflow_name")

                wr = workflow_runs_collection.find_one(
                    {"workflow.workflow_name": workflow_name}
                )

                if wr:
                    be = benchmark_execution_collection.find_one(
                        {"_id": ObjectId(wr["benchmark_execution_id"])}
                    )

            if not be:
                return failed("Data not found for given id", 404)

            result = build_response(be, job_status)

            if search and not match_search(result, search):
                return failed("No matching data found", 404)

            if job_status and not result.get("jobs"):
                return failed("No jobs found with given status", 404)

            return success("Data fetched successfully", result)

        all_data = benchmark_execution_collection.find()
        result = []

        for doc in all_data:
            res = build_response(doc, job_status)

            if search and not match_search(res, search):
                continue

            if job_status:
                if res.get("jobs"):
                    result.append(res)
            else:
                result.append(res)

        if search and not result:
            return failed("No matching data found", 404)

        if job_status and not result:
            return failed("No data found for given job status", 404)

        return success("Data fetched successfully", result)

    except InvalidId:
        return failed("Invalid id provided", 400)
    except Exception as e:
        return failed(str(e), 500)