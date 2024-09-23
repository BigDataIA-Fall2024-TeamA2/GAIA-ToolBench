import logging

from sqlalchemy import Engine

from .benchmark_results import Base as OperationsBase
from .test_cases import Base as TestBase

logger = logging.getLogger(__name__)

def create_tables(engine: Engine):
    TestBase.metadata.create_all(engine)
    OperationsBase.metadata.create_all(engine)
    logger.info("Created table `benchmark_results` and `test_cases`")
