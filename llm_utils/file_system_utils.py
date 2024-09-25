import os

RESOURCES_PATH = "resources/"

def get_file(file_path: str) -> str:
    """
    Check if file exists in local file system and download from S3 if it is missing
    :param file_path:
    :return:
    """
    if not os.path.exists(file_path):
        ...
