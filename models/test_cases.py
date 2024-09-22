from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class TestCasesModel(Base):
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