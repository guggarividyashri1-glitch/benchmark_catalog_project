
from pydantic import BaseModel
from typing import List, Dict


class ResultDetail(BaseModel):
    success: bool
    message: str
    error: str


class JobResultModel(BaseModel):
    result: List[Dict[str, ResultDetail]]