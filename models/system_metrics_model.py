from pydantic import BaseModel, Field, IPvAnyAddress

class SystemMetrics(BaseModel):
    cpu_usage: float = Field(..., ge=0)
    memory_usage: float = Field(..., ge=0)
    bytes_sent: int = Field(..., ge=0)
    bytes_received: int = Field(..., ge=0)
    ip_address: IPvAnyAddress

    server_name: str = Field(..., min_length=1)
    os: str = Field(..., min_length=1)