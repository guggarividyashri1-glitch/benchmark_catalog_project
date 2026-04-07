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
        updated_stages = []

        for stage in updated_workflow["stages"]:
            updated_tasks = []

            for task in stage["tasks"]:
                job_doc = {
                    "stage_type": stage["stage_type"],
                    "stage_name": stage["stage_name"],
                    "stage_order": stage["stage_order"],
                    "task_type": task["task_type"],
                    "task_name": task["task_name"],
                    "task_order": task["task_order"],

                    "job_status": "queued",
                    "started_at": None,
                    "finished_at": None,
                    "created_on": datetime.utcnow()
                }

                job_result = job_collection.insert_one(job_doc)
                job_id = str(job_result.inserted_id)

                updated_task = dict(task)
                updated_task["job_id"] = job_id

                updated_tasks.append(updated_task)

            updated_stage = dict(stage)
            updated_stage["tasks"] = updated_tasks

            updated_stages.append(updated_stage)

        updated_workflow["stages"] = updated_stages

        be_data = {k: v for k, v in data.items() if k != "workflow"}
        be_data["workflow"] = updated_workflow

        be_id = benchmark_execution_collection.insert_one(be_data).inserted_id

        wr_data = {k: v for k, v in data.items() if k != "save_to_workflow_catalog"}
        wr_data["workflow"] = updated_workflow
        wr_data["created_on"] = datetime.utcnow()
        wr_data["created_by"] = user_email

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
                "catalog_name": updated_workflow["workflow_name"],
                "benchmark_name": data.get("benchmark_name"),
                "workflow_name": updated_workflow["workflow_name"],
                "visibility": updated_workflow["visibility"],
                "workflow_data": updated_workflow,  
                "created_on": datetime.utcnow(),
                "created_by": user_email
            })

        return success("Data inserted successfully")

    except Exception as e:
        return failed(str(e), 500)