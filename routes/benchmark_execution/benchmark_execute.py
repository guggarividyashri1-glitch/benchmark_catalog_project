from fastapi import APIRouter
from datetime import datetime

from models.benchmark_execute_model import BenchmarkExecute
from config.database import (
    benchmark_execution_collection,
    workflow_runs_collection,
    workflow_catalog_collection,
    job_collection
)
from utils.response import success, failed

router = APIRouter(tags=["Benchmark Execution"])


@router.post("/benchmark/execute")
def execute_benchmark(payload: BenchmarkExecute):
    try:
        data = payload.model_dump()
        user_email = "system"
        updated_workflow = dict(data["workflow"])

        for stage in updated_workflow.get("stages", []):
            for task in stage.get("tasks", []):

                job_doc = {
                    "stage_type": stage.get("stage_type"),
                    "stage_name": stage.get("stage_name"),
                    "stage_order": stage.get("stage_order"),
                    "task_type": task.get("task_type"),
                    "task_name": task.get("task_name"),
                    "task_order": task.get("task_order"),

                    "job_status": "queued",
                    "started_at": None,
                    "finished_at": None,
                    "created_on": datetime.utcnow()
                }

                job_result = job_collection.insert_one(job_doc)
                job_id = str(job_result.inserted_id)

                task["job_id"] = job_id
        be_data = {k: v for k, v in data.items() if k != "workflow"}
        be_data["created_on"] = datetime.utcnow()

        be_id = benchmark_execution_collection.insert_one(be_data).inserted_id

        wr_data = {
            "benchmark_name": data.get("benchmark_name"),
            "workflow": updated_workflow,   
            "created_on": datetime.utcnow(),
            "created_by": user_email
        }

        wr_id = workflow_runs_collection.insert_one(wr_data).inserted_id

        benchmark_execution_collection.update_one(
            {"_id": be_id},
            {"$set": {"workflow_runs_id": str(wr_id)}}
        )

        workflow_runs_collection.update_one(
            {"_id": wr_id},
            {"$set": {"benchmark_execution_id": str(be_id)}}
        )

        job_collection.update_many(
            {"workflow_run_id": {"$exists": False}},
            {
                "$set": {
                    "workflow_run_id": str(wr_id),
                    "benchmark_execution_id": str(be_id)
                }
            }
        )

        if data.get("save_to_workflow_catalog"):
            workflow_catalog_collection.insert_one({
                "catalog_name": updated_workflow.get("workflow_name"),
                "benchmark_name": data.get("benchmark_name"),
                "workflow_name": updated_workflow.get("workflow_name"),
                "visibility": updated_workflow.get("visibility"),
                "workflow_data": updated_workflow,  
                "created_on": datetime.utcnow(),
                "created_by": user_email
            })

        return success("Data inserted successfully")

    except Exception as e:
        return failed(str(e), 500)