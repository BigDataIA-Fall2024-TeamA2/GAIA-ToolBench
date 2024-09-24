import glob
import logging
import os

from botocore.exceptions import ClientError

from utils.s3 import load_s3_bucket, get_s3_client

logger = logging.getLogger(__name__)
ATTACHMENTS_DIRECTORY = "resources/file_attachments"


def main():
    bucket_name = load_s3_bucket()
    files_list = glob.glob(ATTACHMENTS_DIRECTORY + "/*")

    for idx, file in enumerate(files_list):
        success = upload_file(file, bucket_name)
        if not success:
            logger.error(f"Failed to upload {idx} | {file}")


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = get_s3_client()
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


if __name__ == "__main__":
    main()
