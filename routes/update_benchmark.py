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
@router.patch("/benchmark/update/{id}")
def update_benchmark(id: str, payload: dict):

    try:
        try:
            obj_id = ObjectId(id)
        except InvalidId:
            return failed("Invalid id provided", 400)

        be_doc = None
        wr_doc = None
        wc_doc = None

        be_doc = benchmark_execution_collection.find_one({"_id": obj_id})

        if be_doc and "workflow_runs_id" in be_doc:
            wr_doc = workflow_runs_collection.find_one(
                {"_id": ObjectId(be_doc["workflow_runs_id"])}
            )

        if not be_doc:
            wr_doc = workflow_runs_collection.find_one({"_id": obj_id})

            if wr_doc and "benchmark_execution_id" in wr_doc:
                be_doc = benchmark_execution_collection.find_one(
                    {"_id": ObjectId(wr_doc["benchmark_execution_id"])}
                )

        if not be_doc and not wr_doc:
            wc_doc = workflow_catalog_collection.find_one({"_id": obj_id})

            if wc_doc:
                workflow_name = wc_doc.get("workflow_data", {}).get("workflow_name")

                wr_doc = workflow_runs_collection.find_one(
                    {"workflow.workflow_name": workflow_name}
                )

                if wr_doc and "benchmark_execution_id" in wr_doc:
                    be_doc = benchmark_execution_collection.find_one(
                        {"_id": ObjectId(wr_doc["benchmark_execution_id"])}
                    )

        if not be_doc:
            return failed("No matching data found for given id", 404)

        if wr_doc and not wc_doc:
            workflow_name = wr_doc.get("workflow", {}).get("workflow_name")
            if workflow_name:
                wc_doc = workflow_catalog_collection.find_one(
                    {"workflow_data.workflow_name": workflow_name}
                )

        update_data = {k: v for k, v in payload.items() if v is not None}

        if not update_data:
            return failed("No data provided for update", 400)

        be_update = {}
        wr_update = {}
        wc_update = {}

        for key, value in update_data.items():

            if key in be_doc and be_doc.get(key) != value:
                be_update[key] = value

            if wr_doc:
                if key.startswith("workflow."):
                    wr_update[key] = value
                elif key in wr_doc and wr_doc.get(key) != value:
                    wr_update[key] = value

            if wc_doc:
                if key.startswith("workflow."):
                    new_key = key.replace("workflow.", "workflow_data.")
                    wc_update[new_key] = value
                elif key in wc_doc and wc_doc.get(key) != value:
                    wc_update[key] = value

        if not be_update and not wr_update and not wc_update:
            return failed("Data has not changed", 400)

        now = datetime.utcnow()

        if be_update:
            be_update["updated_on"] = now

        if wr_update:
            wr_update["updated_on"] = now

        if wc_update:
            wc_update["updated_on"] = now

        modified = False

        if be_update:
            result = benchmark_execution_collection.update_one(
                {"_id": be_doc["_id"]},
                {"$set": be_update}
            )
            if result.modified_count > 0:
                modified = True

        if wr_doc and wr_update:
            result = workflow_runs_collection.update_one(
                {"_id": wr_doc["_id"]},
                {"$set": wr_update}
            )
            if result.modified_count > 0:
                modified = True

        if wc_doc and wc_update:
            result = workflow_catalog_collection.update_one(
                {"_id": wc_doc["_id"]},
                {"$set": wc_update}
            )
            if result.modified_count > 0:
                modified = True

        if not modified:
            return failed("Data has not changed", 400)

        return success("Data updated successfully across all collections")

    except Exception as e:
        return failed(str(e), 500)