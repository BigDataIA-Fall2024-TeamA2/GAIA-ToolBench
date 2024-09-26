import os
import unittest
from unittest.mock import patch, MagicMock
import utils.file_system_utils as fsu
from botocore.exceptions import ClientError


class TestFileSystemUtils(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_load_aws_tokens_missing_env(self):
        """Test load_aws_tokens when environment variables are missing"""
        with self.assertRaises(ValueError):
            fsu.load_aws_tokens()

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_access_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret_key",
        "AWS_REGION": "test_region"
    })
    def test_load_aws_tokens_success(self):
        """Test load_aws_tokens when environment variables are set"""
        result = fsu.load_aws_tokens()
        expected = {
            "aws_access_key_id": "test_access_key",
            "aws_secret_access_key": "test_secret_key",
            "region_name": "test_region"
        }
        self.assertEqual(result, expected)

    @patch.dict(os.environ, {}, clear=True)
    def test_load_s3_bucket_missing_env(self):
        """Test load_s3_bucket when environment variable is missing"""
        with self.assertRaises(ValueError):
            fsu.load_s3_bucket()

    @patch.dict(os.environ, {"AWS_S3_BUCKET": "test-bucket"})
    def test_load_s3_bucket_success(self):
        """Test load_s3_bucket when environment variable is set"""
        result = fsu.load_s3_bucket()
        self.assertEqual(result, "test-bucket")

    @patch('file_system_utils.boto3.client')
    @patch('file_system_utils.load_aws_tokens', return_value={
        "aws_access_key_id": "test_access_key",
        "aws_secret_access_key": "test_secret_key",
        "region_name": "test_region"
    })
    def test_get_s3_client(self, mock_load_tokens, mock_boto_client):
        """Test get_s3_client returns a valid boto3 client"""
        fsu.get_s3_client()
        mock_boto_client.assert_called_once_with("s3", aws_access_key_id="test_access_key",
                                                 aws_secret_access_key="test_secret_key",
                                                 region_name="test_region")

    @patch('file_system_utils.download')
    @patch('file_system_utils.os.path.exists', return_value=False)
    @patch('file_system_utils.read_file_contents')
    def test_load_file_without_picture_format(self, mock_read, mock_exists, mock_download):
        """Test load_file when the file does not have a picture format"""
        mock_download.return_value = True
        mock_read.return_value = b"file content"
        key = "test.txt"
        content, path = fsu.load_file(key)
        mock_download.assert_called_once_with(key)
        mock_read.assert_called_once()
        self.assertEqual(content, b"file content")
        self.assertEqual(path, os.path.join(fsu.LOCAL_CACHE_DIRECTORY, key))

    @patch('file_system_utils.download', return_value=False)
    @patch('file_system_utils.os.path.exists', return_value=False)
    @patch('file_system_utils.get_s3_client')
    def test_download_file_not_found(self, mock_s3_client, mock_exists, mock_download):
        """Test download when file is not found on S3"""
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadObject"
        )

        result = fsu.download("non_existent_file.txt")
        mock_s3.head_object.assert_called_once()
        self.assertFalse(result)

    @patch('file_system_utils.get_s3_client')
    @patch('file_system_utils.load_s3_bucket', return_value='test-bucket')
    @patch('file_system_utils.os.path.exists', return_value=False)
    def test_download_file_success(self, mock_exists, mock_s3_bucket, mock_s3_client):
        """Test download when file is successfully downloaded from S3"""
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3
        mock_s3.head_object.return_value = {}

        result = fsu.download("test.txt")
        mock_s3.download_file.assert_called_once_with(
            'test-bucket', 'test.txt', os.path.join(fsu.LOCAL_CACHE_DIRECTORY, 'test.txt')
        )
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
