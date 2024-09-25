from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base

from models.db import db_session

Base = declarative_base()


class TestCases(Base):
    __tablename__ = "test_cases"

    index = Column(Integer())
    task_id = Column(String(36), primary_key=True)
    question = Column(String(2100), nullable=False)
    level = Column(Integer(), nullable=False)
    answer = Column(String(130), nullable=False)
    file_name = Column(String(45), nullable=True)
    file_path = Column(String(250), nullable=True)
    metadata_steps = Column(Text, nullable=False)
    metadata_num_steps = Column(String(), nullable=False)
    metadata_time_taken = Column(String(30), nullable=False)
    metadata_tools = Column(String(115), nullable=False)
    metadata_num_tools = Column(Integer(), nullable=True)
    created_at = Column(DateTime(), default=datetime.now)
    modified_at = Column(DateTime(), default=datetime.now)


def fetch_all_tests():
    with db_session() as session:
        return session.query(
            TestCases.index,
            TestCases.task_id,
            TestCases.question,
            TestCases.file_name,
            TestCases.file_path,
            TestCases.answer,
            TestCases.metadata_steps
        ).all()


def fetch_test_by_id(task_id: str):
    with db_session() as session:
        return session.query(TestCases).filter(TestCases.task_id == task_id).first()
