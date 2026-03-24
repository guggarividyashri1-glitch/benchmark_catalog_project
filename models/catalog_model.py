from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Dict
import re

class Scripts(BaseModel):

    sut_teardown: str
    sut_setup: str
    lts_teardown: Optional[str] = None
    lts_setup: Optional[str] = None

    @field_validator("sut_teardown")
    def validate_sut_teardown(cls, v):

        if not v:
            raise ValueError("sut_teardown is mandatory")

        return v
    @field_validator("sut_setup")
    def validate_sut_setup(cls, v):

        if not v:
            raise ValueError("sut_setup is mandatory")

        return v

class SutLtsConfig(BaseModel):

    sut: Optional[str] = None
    lts: Optional[str] = None

class Catalog(BaseModel):

    catalog_name: str
    benchmark_name: str
    benchmark_category: str
    description: Optional[str] = None

    scripts: Scripts

    run_parameters: Dict

    metrics: List[str]

    tags: Optional[List[str]] = None

    enable_lts_mode: Optional[bool] = False

    sut_lts_config: Optional[SutLtsConfig] = None

    visibility: str

    @field_validator("catalog_name")
    def validate_catalog(cls, v):

        if not v:
            raise ValueError("catalog name is missing")

        if re.search(r'\d', v):
            raise ValueError("catalog_name should not contain numbers")

        return v

    @field_validator("benchmark_name")
    def validate_benchmark(cls, v):

        if not v:
            raise ValueError("benchmark_name is required")

        if re.search(r'\d', v):
            raise ValueError("benchmark_name should not contain numbers")

        return v

    @field_validator("benchmark_category")
    def validate_category(cls, v):

        if not v:
            raise ValueError("benchmark_category is required")

        if re.search(r'\d', v):
            raise ValueError("benchmark_category should not contain numbers")

        return v

    @field_validator("run_parameters")
    def validate_run_parameters(cls, v):

        if not v or len(v.keys()) == 0:
            raise ValueError("run_parameters must contain at least one parameter")

        return v

    @field_validator("metrics")
    def validate_metrics(cls, v):

        if not v or len(v) == 0:
            raise ValueError("metrics should not be empty")

        return v

    @model_validator(mode="after")
    def validate_lts_scripts(self):

        if self.enable_lts_mode:

            if not self.scripts.lts_teardown:
                raise ValueError(
                    "lts_teardown is required when enable_lts_mode is True"
                )

            if not self.scripts.lts_setup:
                raise ValueError(
                    "lts_setup is required when enable_lts_mode is True"
                )

        return self

    @model_validator(mode="after")
    def validate_lts_config(self):
        if self.enable_lts_mode:
            if not self.sut_lts_config:
                raise ValueError(
                    "sut_lts_config is required when enable_lts_mode is True"
                    )

            if not self.sut_lts_config.sut:
                raise ValueError(
                    "sut must be provided when enable_lts_mode is True"
                    )

            if not self.sut_lts_config.lts:
                raise ValueError(
                    "lts must be provided when enable_lts_mode is True"
                    )

            if self.sut_lts_config.sut not in ["windows", "linux"]:
                raise ValueError(
                    "sut must be either windows or linux"
                    )

            if self.sut_lts_config.lts not in ["windows", "linux"]:
                raise ValueError(
                     "lts must be either windows or linux"
                    )
        return self

    @field_validator("visibility")
    def validate_visibility(cls, v):

        if v not in ["public", "private"]:
            raise ValueError("visibility must be public or private")

        return v