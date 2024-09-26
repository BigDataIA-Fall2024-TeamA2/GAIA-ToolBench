from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base

from models.db import db_session

Base = declarative_base()


class BenchmarkResults(Base):
    __tablename__ = "benchmark_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    llm_answer = Column(Text)
    is_cot = Column(Boolean)
    model_name = Column(String)
    prompted_question = Column(String(2100))
    # task_id = mapped_column(ForeignKey("test_cases.task_id"))  # TODO: Add foreign key
    task_id = Column(String(36))
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(), default=datetime.now)


def create_benchmark_result(
    llm_answer: str,
    is_cot: bool,
    model_name: str,
    prompted_question: str,
    task_id: str,
    status: str,
):
    with db_session() as session:
        new_benchmark_result = BenchmarkResults(
            llm_answer=llm_answer,
            is_cot=is_cot,
            model_name=model_name,
            prompted_question=prompted_question,
            task_id=task_id,
            status=status,
        )
        session.add(new_benchmark_result)
        session.commit()
        return new_benchmark_result
    
def fetch_benchmark_results():
    with db_session() as session:
        results = session.query(BenchmarkResults).all()
        return results