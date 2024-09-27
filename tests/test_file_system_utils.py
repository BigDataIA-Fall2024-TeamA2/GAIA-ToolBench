import unittest
from unittest.mock import patch, MagicMock
import os
import boto3
from botocore.exceptions import ClientError

# Import the functions to be tested
from utils.file_system_utils import (
    load_aws_tokens,
    load_s3_bucket,
    get_s3_client,
    load_file,
    read_file_contents,
    download,
    LOCAL_CACHE_DIRECTORY,
    FILE_FORMATS_WITH_PICTURES
)

class TestS3Functions(unittest.TestCase):

    def setUp(self):
        # Set up test environment variables
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_access_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'
        os.environ['AWS_REGION'] = 'test_region'
        os.environ['AWS_S3_BUCKET'] = 'test_bucket'

    def tearDown(self):
        # Clean up environment variables
        for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'AWS_S3_BUCKET']:
            if key in os.environ:
                del os.environ[key]

    def test_load_aws_tokens(self):
        tokens = load_aws_tokens()
        self.assertEqual(tokens['aws_access_key_id'], 'test_access_key')
        self.assertEqual(tokens['aws_secret_access_key'], 'test_secret_key')
        self.assertEqual(tokens['region_name'], 'test_region')

    def test_load_aws_tokens_missing_credentials(self):
        del os.environ['AWS_ACCESS_KEY_ID']
        with self.assertRaises(ValueError):
            load_aws_tokens()

    def test_load_s3_bucket(self):
        bucket = load_s3_bucket()
        self.assertEqual(bucket, 'test_bucket')

    def test_load_s3_bucket_missing(self):
        del os.environ['AWS_S3_BUCKET']
        with self.assertRaises(ValueError):
            load_s3_bucket()

    @patch('boto3.client')
    def test_get_s3_client(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        client = get_s3_client()
        self.assertEqual(client, mock_client)
        mock_boto3_client.assert_called_once_with('s3', **load_aws_tokens())

    @patch('os.path.exists')
    @patch('utils.file_system_utils.download')
    @patch('utils.file_system_utils.read_file_contents')
    def test_load_file(self, mock_read_contents, mock_download, mock_exists):
        mock_exists.return_value = True
        mock_read_contents.return_value = b'test content'
        content, path = load_file('test_file.txt')
        self.assertEqual(content, b'test content')
        self.assertTrue(path.endswith('test_file.txt'))
        mock_download.assert_not_called()

    @patch('os.path.exists')
    @patch('utils.file_system_utils.download')
    @patch('utils.file_system_utils.read_file_contents')
    def test_load_file_with_pictures(self, mock_read_contents, mock_download, mock_exists):
        mock_exists.side_effect = [False, True]  # First call returns False, second call returns True
        mock_download.return_value = True
        mock_read_contents.return_value = b'png content'
        content, path = load_file('test_file.xlsx')
        self.assertEqual(content, b'png content')
        self.assertTrue(path.endswith('test_file.png'))
        mock_download.assert_called_once_with('test_file.png')

    def test_read_file_contents(self):
        with patch('builtins.open', unittest.mock.mock_open(read_data=b'file content')) as mock_file:
            content = read_file_contents('test_file.txt')
            self.assertEqual(content, b'file content')
            mock_file.assert_called_once_with('test_file.txt', 'rb')

    @patch('utils.file_system_utils.get_s3_client')
    @patch('utils.file_system_utils.load_s3_bucket')
    def test_download_success(self, mock_load_bucket, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_load_bucket.return_value = 'test_bucket'

        result = download('test_file.txt')

        self.assertTrue(result)
        mock_client.head_object.assert_called_once_with(Bucket='test_bucket', Key='test_file.txt')
        mock_client.download_file.assert_called_once()

    @patch('utils.file_system_utils.get_s3_client')
    @patch('utils.file_system_utils.load_s3_bucket')
    def test_download_file_not_found(self, mock_load_bucket, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_load_bucket.return_value = 'test_bucket'
        mock_client.head_object.side_effect = ClientError({'Error': {'Code': '404'}}, 'HeadObject')

        result = download('non_existent_file.txt')

        self.assertFalse(result)
        mock_client.head_object.assert_called_once_with(Bucket='test_bucket', Key='non_existent_file.txt')
        mock_client.download_file.assert_not_called()

if __name__ == '__main__':
    unittest.main()
