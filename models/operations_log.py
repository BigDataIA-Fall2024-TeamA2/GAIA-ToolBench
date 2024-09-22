from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

from sqlalchemy.testing.schema import mapped_column

Base = declarative_base()

class BenchmarkResultsModel(Base):
    __tablename__ = "benchmark_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    llm_answer = Column(Text)
    is_cot = Column(Boolean)
    model_name = Column(String)
    # task_id = mapped_column(ForeignKey("test_cases.task_id"))  # TODO: Add foreign key
    task_id = Column(String(36))
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(), default=datetime.now)

"""
test_case
    - Get task_id
    - Get attachment

benchmark_results
    - insert

"""