from fastapi import APIRouter, Query
from bson import ObjectId
from bson.errors import InvalidId
from config.database import (
    benchmark_execution_collection,
    workflow_runs_collection,
    workflow_catalog_collection
)
from utils.response import success, failed

router = APIRouter(tags=["Benchmark Execution"])
def convert_objectid(data):
    return (
        {k: str(v) if isinstance(v, ObjectId) else convert_objectid(v) for k, v in data.items()}
        if isinstance(data, dict)
        else [convert_objectid(i) for i in data] if isinstance(data, list)
        else data
    )
def build_response(be_doc):
    doc = dict(be_doc)
    doc["_id"] = str(doc["_id"])
    wr = (
        doc.get("workflow_runs_id") and
        workflow_runs_collection.find_one(
            {"_id": ObjectId(doc["workflow_runs_id"])}
        )
    )
    doc["workflow"] = (wr and wr.get("workflow")) or doc.get("workflow")
    return convert_objectid(doc)
@router.get("/benchmark/get")
def get_benchmark(id: str = Query(default=None)):
    try:
        obj_id = id and ObjectId(id)
        be = obj_id and benchmark_execution_collection.find_one({"_id": obj_id})
        wr = (
            (not be and obj_id and workflow_runs_collection.find_one({"_id": obj_id}))
            or None
        )
        be = be or (
            wr and wr.get("benchmark_execution_id") and
            benchmark_execution_collection.find_one(
                {"_id": ObjectId(wr["benchmark_execution_id"])}
            )
        )
        wc = (
            (not be and not wr and obj_id and
             workflow_catalog_collection.find_one({"_id": obj_id}))
            or None
        )
        workflow_name = wc and wc.get("workflow_data", {}).get("workflow_name")
        wr = wr or (
            workflow_name and workflow_runs_collection.find_one(
                {"workflow.workflow_name": workflow_name}
            )
        )
        be = be or (
            wr and wr.get("benchmark_execution_id") and
            benchmark_execution_collection.find_one(
                {"_id": ObjectId(wr["benchmark_execution_id"])}
            )
        )
        return (
            be and success("Data fetched successfully", build_response(be))
        ) or (
            id and failed("Data not found for given id", 404)
        ) or (
            success(
                "All benchmark executions fetched successfully",
                [build_response(x) for x in benchmark_execution_collection.find()]
            )
        )
    except InvalidId:
        return failed("Invalid id provided", 400)
    except Exception as e:
        return failed(str(e), 500)