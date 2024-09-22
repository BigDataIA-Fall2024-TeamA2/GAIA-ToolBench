from sqlalchemy import Engine

from .operations_log import Base as OperationsBase
from .test_cases import Base as TestBase

def create_tables(engine: Engine):
    TestBase.metadata.create_all(engine)
    OperationsBase.metadata.create_all(engine)

