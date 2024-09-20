import json
from glob import glob
import pandas as pd
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


def load_datasets_from_filesystem():
    file_list = glob("resources/datasets/validation/*_all.csv")
    dataset_headers = [
        "task_id",
        "question",
        "level",
        "answer",
        "file_name",
        "file_path",
        "annotator_metadata"
    ]
    if len(file_list) == 0:
        raise ValueError("There are no datasets available in the resources path")

    for file in file_list:
        dataset_df = pd.read_csv(file, names=dataset_headers, header=0)
        dataset_df["created_at"] = datetime.now()
        dataset_df["modified_at"] = datetime.now()
        dataset_df["annotator_metadata"] = dataset_df["annotator_metadata"].apply(improve_annotator_metadata)

        # Flatten annotator_metadata fields
        json_struct = json.loads(dataset_df.to_json(orient="records"))
        flattened_dataset_df = pd.json_normalize(json_struct)
        flattened_dataset_df.to_csv("resources/cleaned_datasets/1.csv", index=False)


def preprocess_annotator_metadata(metadata: str) -> str:
    # logger.info("Fixing annotator metadata")
    global failures
    failures += 1
    return json.loads(
        metadata
        .replace("\'", "'")
        .replace('"', "TEMP")
        .replace("'", '"')
        .replace("TEMP", "'")
    )


def transfer_attachment(source_file_path: str) -> str:
    """
    Download the file attachments from Hugging Face dataset cache and upload to S3
    :param source_file_path:
    :return:
    """
    # TODO: Do last
    ...


if __name__ == "__main__":
    load_datasets_from_filesystem()
