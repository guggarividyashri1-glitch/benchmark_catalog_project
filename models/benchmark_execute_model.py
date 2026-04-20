from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Any

def not_empty_string(value: str, field_name: str):
    if not value or value.strip() == "":
        raise ValueError(f"{field_name} should not be empty")
    return value


def validate_number(value, field_name: str):
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must contain numbers only")
    return value


def not_empty_dict(value: Dict, field_name: str):
    if value is None or len(value) == 0:
        raise ValueError(f"{field_name} should not be empty")
    return value


def validate_string_list(value: List, field_name: str):
    if value is None or len(value) == 0:
        raise ValueError(f"{field_name} should not be empty")

    for item in value:
        if not isinstance(item, str) or item.strip() == "":
            raise ValueError(f"{field_name} should not contain empty values")

    return value

class Task(BaseModel):
    task_type: str
    task_name: str
    task_order: int

    @model_validator(mode="after")
    def validate_task(self):
        not_empty_string(self.task_type, "task_type")
        not_empty_string(self.task_name, "task_name")
        validate_number(self.task_order, "task_order")
        return self
    
class Stage(BaseModel):
    stage_type: str
    stage_name: str
    stage_order: int

    tasks: List[Task]   

    executor: Dict[str, Any]
    parameters: Dict[str, Any]
    parameters_schema: Dict[str, Any]

    visibility: List[str]
    target_sut: List[str]

    @model_validator(mode="after")
    def validate_stage(self):
        not_empty_string(self.stage_type, "stage_type")
        not_empty_string(self.stage_name, "stage_name")
        validate_number(self.stage_order, "stage_order")

        if not self.tasks:
            raise ValueError("tasks should not be empty")

        not_empty_dict(self.executor, "executor")
        not_empty_dict(self.parameters, "parameters")
        not_empty_dict(self.parameters_schema, "parameters_schema")

        validate_string_list(self.visibility, "visibility")
        validate_string_list(self.target_sut, "target_sut")

        return self

class Workflow(BaseModel):
    stages: List[Stage]
    workflow_name: str
    visibility: str

    @model_validator(mode="after")
    def validate_workflow(self):
        not_empty_string(self.workflow_name, "workflow_name")
        not_empty_string(self.visibility, "workflow visibility")

        if not self.stages:
            raise ValueError("stages should not be empty")

        return self

class ScheduleTest(BaseModel):
    test_name: str

    @field_validator("test_name")
    def validate_test_name(cls, v):
        return not_empty_string(v, "test_name")


class ScheduleDetails(BaseModel):
    date: str
    time: str
    no_of_runs: int
    iteration_per_run: int
    cores_per_instance: int

    @model_validator(mode="after")
    def validate_schedule(self):
        not_empty_string(self.date, "date")
        not_empty_string(self.time, "time")

        validate_number(self.no_of_runs, "no_of_runs")
        validate_number(self.iteration_per_run, "iteration_per_run")
        validate_number(self.cores_per_instance, "cores_per_instance")

        return self

class BenchmarkExecute(BaseModel):
    benchmark_name: str
    benchmark_category: str
    catalog_name: str

    group_id: str
    environment: str

    schedule_test: ScheduleTest
    schedule_details: ScheduleDetails

    no_of_sut: int

    workflow: Workflow

    save_to_workflow_catalog: bool

    custom_tags: List[str]

    @model_validator(mode="after")
    def validate_main(self):
        not_empty_string(self.benchmark_name, "benchmark_name")
        not_empty_string(self.benchmark_category, "benchmark_category")
        not_empty_string(self.catalog_name, "catalog_name")

        not_empty_string(self.group_id, "group_id")
        not_empty_string(self.environment, "environment")

        validate_number(self.no_of_sut, "no_of_sut")
        validate_string_list(self.custom_tags, "custom_tags")

        return self