from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    stage_type: str = Field(...)
    stage_name: str = Field(...)
    stage_order: int = Field(...)
    task_type: str = Field(...)
    task_name: str = Field(...)
    task_order: int = Field(...)
    job_status: Optional[str] = "queued"

    @field_validator("stage_type", "stage_name", "task_type", "task_name")
    def fields_not_empty(cls, value, info):
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} should not be empty")
        return value

    @field_validator("stage_order", "task_order")
    def order_must_be_number(cls, value, info):
        if not isinstance(value, int):
            raise ValueError(f"{info.field_name} must be a number")
        return value