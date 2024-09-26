import logging
import os

import boto3
from botocore.exceptions import ClientError

LOCAL_CACHE_DIRECTORY = os.path.join("resources", "benchmark_attachments")
OPENAI_SUPPORTED_FILE_FORMATS = [
    ".c",
    ".cpp",
    ".css",
    ".csv",
    ".docx",
    ".gif",
    ".go",
    ".html",
    ".java",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".md",
    ".pdf",
    ".php",
    ".pkl",
    ".png",
    ".pptx",
    ".py",
    ".rb",
    ".tar",
    ".tex",
    ".ts",
    ".txt",
    ".webp",
    ".xlsx",
    ".xml",
    ".zip",
]
FILE_FORMATS_WITH_PICTURES = [".xlsx", ".pdf"]

logger = logging.getLogger(__name__)

# TODO: Update all the file paths to be absolute and not relative


def load_aws_tokens():
    if all(
        [
            k in os.environ
            for k in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
        ]
    ):
        return {
            "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
            "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "region_name": os.environ["AWS_REGION"],
        }
    raise ValueError("Missing AWS Credentials in environment")


def load_s3_bucket():
    if "AWS_S3_BUCKET" in os.environ:
        return os.environ["AWS_S3_BUCKET"]
    raise ValueError("Missing AWS S3 Bucket")


def get_s3_client():
    return boto3.client("s3", **load_aws_tokens())


def load_file(key: str) -> (bytes, str):
    local_path = os.path.join(LOCAL_CACHE_DIRECTORY, os.path.basename(key))
    _, ext = os.path.splitext(local_path)

    # If the file is of the complex file format, then prefer to use the picture (.png) file of the file
    if ext in FILE_FORMATS_WITH_PICTURES:
        updated_local_path = local_path.replace(ext, ".png")
        if not os.path.exists(updated_local_path):
            success = download(key.replace(ext, ".png"))
            if success:
                logger.info(
                    f"Using the .png file instead of the actual source file: {key}"
                )
                return read_file_contents(updated_local_path), updated_local_path

    if not os.path.exists(local_path):
        download(key)
    return read_file_contents(local_path), local_path


def read_file_contents(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()


def download(key: str):
    s3_client = get_s3_client()
    filename = os.path.basename(key)
    try:
        _ = s3_client.head_object(Bucket=load_s3_bucket(), Key=filename)
        # TODO: DEBUG the path error here
        s3_client.download_file(
            load_s3_bucket(),
            filename,
            os.path.join(LOCAL_CACHE_DIRECTORY, filename),
        )
        logger.info(f"Downloaded file {key} from S3")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":  # File not found
            logger.error(f"File {key} not found on S3")
            return False
        else:
            logger.error("")
            return False
