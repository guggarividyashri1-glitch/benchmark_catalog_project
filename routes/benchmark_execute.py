from fastapi import APIRouter
from datetime import datetime

from models.benchmark_execute_model import BenchmarkExecute
from config.database import (
    benchmark_execution_collection,
    workflow_runs_collection,
    workflow_catalog_collection
)
from utils.response import success, failed

router = APIRouter(tags=["Benchmark Execution"])
@router.post("/benchmark/execute")
def execute_benchmark(payload: BenchmarkExecute):

    try:
        data = payload.model_dump()

        user_email = "system"
        benchmark_execution_data = data.copy()
        benchmark_execution_data.pop("workflow")

        be_result = benchmark_execution_collection.insert_one(benchmark_execution_data)
        benchmark_execution_id = str(be_result.inserted_id)

        workflow_runs_data = data.copy()
        workflow_runs_data.pop("save_to_workflow_catalog")

        workflow_runs_data["created_on"] = datetime.utcnow()
        workflow_runs_data["created_by"] = user_email

        wr_result = workflow_runs_collection.insert_one(workflow_runs_data)
        workflow_runs_id = str(wr_result.inserted_id)

        benchmark_execution_collection.update_one(
            {"_id": be_result.inserted_id},
            {
                "$set": {
                    "workflow_runs_id": workflow_runs_id
                }
            }
        )

        workflow_runs_collection.update_one(
            {"_id": wr_result.inserted_id},
            {
                "$set": {
                    "benchmark_execution_id": benchmark_execution_id
                }
            }
        )

        if data["save_to_workflow_catalog"]:

            workflow_catalog_data = {
                "workflow_name": data["workflow"]["workflow_name"],
                "visibility": data["workflow"]["visibility"],
                "workflow_data": data["workflow"],
                "created_on": datetime.utcnow(),
                "created_by": user_email
            }

            workflow_catalog_collection.insert_one(workflow_catalog_data)

        return success("Data inserted successfully")

    except Exception as e:
        return failed(str(e), 500)