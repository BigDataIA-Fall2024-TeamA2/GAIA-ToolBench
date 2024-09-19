from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OperationsLogModel(BaseModel):
    operation_id: int
    task_id: int
    status: str
    execution_time: Optional[float] = None
    log_details: Optional[str] = None
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True
