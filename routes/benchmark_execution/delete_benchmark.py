from fastapi import APIRouter
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from config.database import (
    benchmark_execution_collection,
    workflow_runs_collection,
    workflow_catalog_collection
)
from utils.response import success, failed
router = APIRouter(tags=["Benchmark Execution"])
def get_active_doc(col, query):
    return col.find_one({**query, "deleted": {"$ne": True}})
@router.delete("/benchmark/delete/{id}")
def delete_benchmark(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        return failed("Invalid id provided", 400)

    try:
        be_exists = benchmark_execution_collection.find_one({"_id": obj_id})
        wr_exists = workflow_runs_collection.find_one({"_id": obj_id})
        wc_exists = workflow_catalog_collection.find_one({"_id": obj_id})

        be_doc = get_active_doc(benchmark_execution_collection, {"_id": obj_id})

        wr_doc = (
            be_doc and be_doc.get("workflow_runs_id") and
            get_active_doc(
                workflow_runs_collection,
                {"_id": ObjectId(be_doc["workflow_runs_id"])}
            )
        ) or get_active_doc(workflow_runs_collection, {"_id": obj_id})

        be_doc = be_doc or (
            wr_doc and wr_doc.get("benchmark_execution_id") and
            get_active_doc(
                benchmark_execution_collection,
                {"_id": ObjectId(wr_doc["benchmark_execution_id"])}
            )
        )

        wc_doc = get_active_doc(workflow_catalog_collection, {"_id": obj_id})

        name = (
            (wc_doc and wc_doc.get("workflow_data", {}).get("workflow_name")) or
            (wr_doc and wr_doc.get("workflow", {}).get("workflow_name"))
        )

        wr_doc = wr_doc or (
            name and get_active_doc(
                workflow_runs_collection,
                {"workflow.workflow_name": name}
            )
        )

        be_doc = be_doc or (
            wr_doc and wr_doc.get("benchmark_execution_id") and
            get_active_doc(
                benchmark_execution_collection,
                {"_id": ObjectId(wr_doc["benchmark_execution_id"])}
            )
        )

        wc_doc = wc_doc or (
            name and get_active_doc(
                workflow_catalog_collection,
                {"workflow_data.workflow_name": name}
            )
        )

        (be_doc or wr_doc or wc_doc) or (_ for _ in ()).throw(
            Exception(
                "Already deleted" if (be_exists or wr_exists or wc_exists)
                else "Data not found"
            )
        )

        now = datetime.utcnow()

        def soft_delete(col, doc):
            return (
                doc and col.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"deleted": True, "deleted_on": now}}
                )
            )
        
        list(map(lambda x: soft_delete(*x), [
            (benchmark_execution_collection, be_doc),
            (workflow_runs_collection, wr_doc),
            (workflow_catalog_collection, wc_doc)
        ]))

        return success("Data deleted successfully across all collections")

    except Exception as e:
        return failed(f"Delete failed: {str(e)}", 500)