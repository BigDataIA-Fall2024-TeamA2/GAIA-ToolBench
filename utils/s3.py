import os

import boto3
from botocore.exceptions import ClientError

LOCAL_CACHE_DIRECTORY = "resources/benchmark_attachments/"


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


def load_file(key: str):
    local_path = os.path.join(LOCAL_CACHE_DIRECTORY, os.path.basename(key))
    if not os.path.exists(local_path):
        download(key)
    return open(local_path, "rb")


def download(key: str):
    s3_client = get_s3_client()
    try:
        s3_client.download_file(
            load_s3_bucket(), key, os.path.join(LOCAL_CACHE_DIRECTORY, os.path.basename(key)),
        )
    except ClientError as e:
        print(e)
