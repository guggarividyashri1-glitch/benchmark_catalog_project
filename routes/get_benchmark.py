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
    if isinstance(data, dict):
        return {k: str(v) if isinstance(v, ObjectId) else convert_objectid(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_objectid(i) for i in data]
    return data
def build_response(be_doc):
    doc = dict(be_doc)
    doc["_id"] = str(doc["_id"])

    if "workflow_runs_id" in doc:
        wr = workflow_runs_collection.find_one(
            {"_id": ObjectId(doc["workflow_runs_id"])}
        )
        if wr and "workflow" in wr:
            doc["workflow"] = wr["workflow"]

    return convert_objectid(doc)

@router.get("/benchmark/get")
def get_benchmark(id: str = Query(default=None)):

    try:
        if id:
            try:
                obj_id = ObjectId(id)
            except InvalidId:
                return failed("Invalid id provided", 400)
            be = benchmark_execution_collection.find_one({"_id": obj_id})
            if be:
                return success(
                    "Data fetched using benchmark_execution id",
                    build_response(be)
                )

            wr = workflow_runs_collection.find_one({"_id": obj_id})
            if wr and "benchmark_execution_id" in wr:
                try:
                    be = benchmark_execution_collection.find_one(
                        {"_id": ObjectId(wr["benchmark_execution_id"])}
                    )
                    if be:
                        return success(
                            "Data fetched using workflow_runs id",
                            build_response(be)
                        )
                except:
                    pass

            wc = workflow_catalog_collection.find_one({"_id": obj_id})
            if wc and "workflow_data" in wc:
                workflow_name = wc["workflow_data"].get("workflow_name")

                wr = workflow_runs_collection.find_one(
                    {"workflow.workflow_name": workflow_name}
                )

                if wr and "benchmark_execution_id" in wr:
                    try:
                        be = benchmark_execution_collection.find_one(
                            {"_id": ObjectId(wr["benchmark_execution_id"])}
                        )
                        if be:
                            return success(
                                "Data fetched using workflow_catalog id",
                                build_response(be)
                            )
                    except:
                        pass

            return failed("Data not found for given id", 404)

        result = []

        for be in benchmark_execution_collection.find():
            result.append(build_response(be))

        return success("All benchmark executions fetched successfully", result)

    except Exception as e:
        return failed(str(e), 500)