from pydantic import BaseModel
from typing import Optional, List, Dict


class UpdateCatalog(BaseModel):

    catalog_name: Optional[str] = None
    benchmark_name: Optional[str] = None
    benchmark_category: Optional[str] = None
    description: Optional[str] = None

    scripts: Optional[dict] = None

    run_parameters: Optional[Dict] = None

    metrics: Optional[List[str]] = None

    tags: Optional[List[str]] = None

    enable_lts_mode: Optional[bool] = None

    sut_lts_config: Optional[dict] = None

    visibility: Optional[str] = None

    