import datasets
import os
from functools import lru_cache
import logging

HUGGING_FACE_DATASET_URI = "gaia-benchmark/GAIA"

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


@lru_cache(maxsize=1)
def load_token() -> str:
    """
    Loads the Hugging Face token from the environment.
    """
    if "HUGGING_FACE_TOKEN" not in os.environ:
        raise ValueError("HUGGING_FACE_TOKEN environment variable not set")
    return os.environ.get("HUGGING_FACE_TOKEN")

def download_datasets() -> bool:
    """
    Downloads a dataset from Hugging Face.
    """
    # TODO: Add error handling
    dataset_configurations = datasets.get_dataset_config_names(path=HUGGING_FACE_DATASET_URI, token=load_token())
    logger.info(f"Loaded {len(dataset_configurations)} dataset configurations for {HUGGING_FACE_DATASET_URI}")
    for config in dataset_configurations:
        src_data: datasets.DatasetDict = datasets.load_dataset(path=HUGGING_FACE_DATASET_URI, token=load_token(), name=config)
        logger.info(f"Loaded {HUGGING_FACE_DATASET_URI}/{config} dataset")
        for dataset_type, dataset in src_data.items():
            dataset.save_to_disk(f"resources/datasets/{config}/{dataset_type}")
    return True


if __name__ == '__main__':
    download_datasets()
