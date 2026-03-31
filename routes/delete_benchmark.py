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

@router.delete("/benchmark/delete/{id}")
def delete_benchmark(id: str):

    try:
        try:
            obj_id = ObjectId(id)
        except InvalidId:
            return failed("Invalid id provided", 400)

        be_doc = None
        wr_doc = None
        wc_doc = None

        # 🔹 Check existing (including deleted)
        be_exists = benchmark_execution_collection.find_one({"_id": obj_id})
        wr_exists = workflow_runs_collection.find_one({"_id": obj_id})
        wc_exists = workflow_catalog_collection.find_one({"_id": obj_id})

        be_doc = benchmark_execution_collection.find_one(
            {"_id": obj_id, "deleted": {"$ne": True}}
        )

        if be_doc:
            if "workflow_runs_id" in be_doc:
                wr_doc = workflow_runs_collection.find_one(
                    {
                        "_id": ObjectId(be_doc["workflow_runs_id"]),
                        "deleted": {"$ne": True}
                    }
                )

        if not be_doc:
            wr_doc = workflow_runs_collection.find_one(
                {"_id": obj_id, "deleted": {"$ne": True}}
            )

            if wr_doc and "benchmark_execution_id" in wr_doc:
                be_doc = benchmark_execution_collection.find_one(
                    {
                        "_id": ObjectId(wr_doc["benchmark_execution_id"]),
                        "deleted": {"$ne": True}
                    }
                )

        if not be_doc and not wr_doc:
            wc_doc = workflow_catalog_collection.find_one(
                {"_id": obj_id, "deleted": {"$ne": True}}
            )

            if wc_doc:
                workflow_name = wc_doc["workflow_data"].get("workflow_name")

                wr_doc = workflow_runs_collection.find_one(
                    {
                        "workflow.workflow_name": workflow_name,
                        "deleted": {"$ne": True}
                    }
                )

                if wr_doc and "benchmark_execution_id" in wr_doc:
                    be_doc = benchmark_execution_collection.find_one(
                        {
                            "_id": ObjectId(wr_doc["benchmark_execution_id"]),
                            "deleted": {"$ne": True}
                        }
                    )

        if wr_doc and not wc_doc:
            workflow_name = wr_doc.get("workflow", {}).get("workflow_name")
            if workflow_name:
                wc_doc = workflow_catalog_collection.find_one(
                    {
                        "workflow_data.workflow_name": workflow_name,
                        "deleted": {"$ne": True}
                    }
                )

        # 🔹 FINAL CHECK (UPDATED LOGIC)
        if not be_doc and not wr_doc and not wc_doc:
            if be_exists or wr_exists or wc_exists:
                return failed("Already deleted", 404)
            else:
                return failed("Data not found", 404)

        current_time = datetime.utcnow()

        if be_doc:
            benchmark_execution_collection.update_one(
                {"_id": be_doc["_id"]},
                {"$set": {"deleted": True, "deleted_on": current_time}}
            )

        if wr_doc:
            workflow_runs_collection.update_one(
                {"_id": wr_doc["_id"]},
                {"$set": {"deleted": True, "deleted_on": current_time}}
            )

        if wc_doc:
            workflow_catalog_collection.update_one(
                {"_id": wc_doc["_id"]},
                {"$set": {"deleted": True, "deleted_on": current_time}}
            )

        return success("Data deleted successfully across all collections")

    except Exception as e:
        return failed(f"Delete failed: {str(e)}", 500)