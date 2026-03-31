from pydantic import BaseModel, Field, IPvAnyAddress

class SystemMetrics(BaseModel):
    cpu_usage: float = Field(..., gt=1, description="CPU usage must be greater than 1")
    memory_usage: float = Field(..., gt=1, description="Memory usage must be greater than 1")
    bytes_sent: int = Field(..., gt=1, description="Bytes sent must be greater than 1")
    bytes_received: int = Field(..., gt=1, description="Bytes received must be greater than 1")

    ip_address: IPvAnyAddress

    server_name: str = Field(..., min_length=1, description="Server name is required")
    os: str = Field(..., min_length=1, description="OS is required")