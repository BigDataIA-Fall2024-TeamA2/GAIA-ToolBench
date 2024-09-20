from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskTypeEnum(str, Enum):
    test = "test"
    validation = "validation"


class TestCaseAnnotatorMetadata(BaseModel):
    steps: str = None
    num_steps: int = 0
    duration: str = None
    tools: list[str] = None
    num_tools: int = 0


class TestCasesModel(BaseModel):
    task_id: int
    question: str
    level: int
    task_type: str = None
    answer: str
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    annotator_metadata: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
