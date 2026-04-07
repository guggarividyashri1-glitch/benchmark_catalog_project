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
def get_related_docs(obj_id):
    be = benchmark_execution_collection.find_one({"_id": obj_id})

    wr = (be and be.get("workflow_runs_id") and
          workflow_runs_collection.find_one({"_id": ObjectId(be["workflow_runs_id"])})) \
         or workflow_runs_collection.find_one({"_id": obj_id})

    be = be or (wr and wr.get("benchmark_execution_id") and
                benchmark_execution_collection.find_one(
                    {"_id": ObjectId(wr["benchmark_execution_id"])}
                ))

    wc = workflow_catalog_collection.find_one({"_id": obj_id})

    name = (wc and wc.get("workflow_data", {}).get("workflow_name")) or \
           (wr and wr.get("workflow", {}).get("workflow_name"))

    wr = wr or (name and workflow_runs_collection.find_one(
        {"workflow.workflow_name": name}
    ))

    be = be or (wr and wr.get("benchmark_execution_id") and
                benchmark_execution_collection.find_one(
                    {"_id": ObjectId(wr["benchmark_execution_id"])}
                ))

    wc = wc or (name and workflow_catalog_collection.find_one(
        {"workflow_data.workflow_name": name}
    ))

    return be, wr, wc
@router.patch("/benchmark/update/{id}")
def update_benchmark(id: str, payload: dict):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        return failed("Invalid id provided", 400)

    try:
        be_doc, wr_doc, wc_doc = get_related_docs(obj_id)

        be_doc or (_ for _ in ()).throw(Exception("No matching data found"))

        update_data = {k: v for k, v in payload.items() if v is not None}
        update_data or (_ for _ in ()).throw(Exception("No data provided"))

        now = datetime.utcnow()

        be_update = {
            k: v for k, v in update_data.items()
            if k in (be_doc or {}) and be_doc.get(k) != v
        }

        wr_update = {
            k: v for k, v in update_data.items()
            if wr_doc and (
                (k.startswith("workflow.") and
                 wr_doc.get("workflow", {}).get(k.split(".", 1)[1]) != v)
                or
                (k in wr_doc and wr_doc.get(k) != v)
            )
        }

        wc_update = {
            (k.replace("workflow.", "workflow_data.") if k.startswith("workflow.") else k): v
            for k, v in update_data.items()
            if wc_doc and (
                (k.startswith("workflow.") and
                 wc_doc.get("workflow_data", {}).get(k.split(".", 1)[1]) != v)
                or
                (k in wc_doc and wc_doc.get(k) != v)
            )
        }

        any([be_update, wr_update, wc_update]) or \
            (_ for _ in ()).throw(Exception("No changes detected: data is same as existing"))

        be_update = be_update and {**be_update, "updated_on": now}
        wr_update = wr_update and {**wr_update, "updated_on": now}
        wc_update = wc_update and {**wc_update, "updated_on": now}

        def apply(col, doc, data):
            return (doc and data and
                    col.update_one(
                        {"_id": doc["_id"]},
                        {"$set": data}
                    ).modified_count) or 0

        modified = sum([
            apply(benchmark_execution_collection, be_doc, be_update),
            apply(workflow_runs_collection, wr_doc, wr_update),
            apply(workflow_catalog_collection, wc_doc, wc_update)
        ])

        modified or (_ for _ in ()).throw(Exception("No changes applied"))

        return success("Data updated successfully across all collections")

    except Exception as e:
        return failed(str(e), 500)