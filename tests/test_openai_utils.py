import pytest
from unittest.mock import patch, MagicMock
from utils.openai_utils import (
    get_openai_client,
    get_assistant_id,
    get_vector_store_id,
    wait_on_run,
    upload_file_to_vectorstore,
    get_openai_response_with_attachments,
    get_openai_response,
    invoke_openai_api
)

def test_get_openai_client():
    with patch.dict('os.environ', {'OPENAI_KEY': 'test_key'}):
        client = get_openai_client()
        assert client.api_key == 'test_key'

def test_get_openai_client_missing_key():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI Key not found in environment variables"):
            get_openai_client()

def test_get_assistant_id():
    with patch.dict('os.environ', {'OPENAI_ASSISTANT_ID': 'test_assistant_id'}):
        assert get_assistant_id() == 'test_assistant_id'

def test_get_assistant_id_missing():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI Assistant ID not found in environment variables"):
            get_assistant_id()

def test_get_vector_store_id():
    with patch.dict('os.environ', {'OPENAI_VECTOR_STORE_ID': 'test_vector_store_id'}):
        assert get_vector_store_id() == 'test_vector_store_id'

def test_get_vector_store_id_missing():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI Vector Store ID not found in environment variables"):
            get_vector_store_id()

def test_wait_on_run_success():
    mock_client = MagicMock()
    mock_run = MagicMock()
    mock_run.status = 'completed'
    mock_thread = MagicMock()

    result = wait_on_run(mock_client, mock_run, mock_thread)
    assert result == mock_run

def test_wait_on_run_failure():
    mock_client = MagicMock()
    mock_run = MagicMock()
    mock_run.status = 'failed'
    mock_thread = MagicMock()

    with pytest.raises(ValueError, match="OpenAI Assistant computing chat completion failed with status: failed"):
        wait_on_run(mock_client, mock_run, mock_thread)

@patch('utils.openai_utils.load_file')
def test_upload_file_to_vectorstore(mock_load_file):
    mock_client = MagicMock()
    mock_client.beta.vector_stores.files.retrieve.side_effect = openai.NotFoundError({})
    mock_load_file.return_value = MagicMock()

    upload_file_to_vectorstore(mock_client, 'test_vector_store_id', 'test_file_path')
    assert mock_client.files.create.called
    assert mock_client.beta.vector_stores.files.upload.called

@patch('utils.openai_utils.get_openai_client')
@patch('utils.openai_utils.get_assistant_id')
@patch('utils.openai_utils.get_vector_store_id')
@patch('utils.openai_utils.load_file')
def test_get_openai_response_with_attachments(mock_load_file, mock_get_vector_store_id, mock_get_assistant_id, mock_get_openai_client):
    mock_client = MagicMock()
    mock_get_openai_client.return_value = mock_client
    mock_get_assistant_id.return_value = 'test_assistant_id'
    mock_get_vector_store_id.return_value = 'test_vector_store_id'
    mock_load_file.return_value = (MagicMock(), 'test_file.txt')

    result = get_openai_response_with_attachments('test_question', 'gpt-4', 'test_file_path')
    assert mock_client.beta.assistants.retrieve.called
    assert mock_client.files.create.called
    assert mock_client.beta.threads.create.called
    assert mock_client.beta.threads.runs.create_and_poll.called

@patch('utils.openai_utils.get_openai_client')
def test_get_openai_response(mock_get_openai_client):
    mock_client = MagicMock()
    mock_get_openai_client.return_value = mock_client
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = 'Test response'
    mock_client.chat.completions.create.return_value = mock_completion

    result = get_openai_response('test_question', 'gpt-4')
    assert result == 'Test response'
    assert mock_client.chat.completions.create.called

@patch('utils.openai_utils.get_openai_response_with_attachments')
@patch('utils.openai_utils.get_openai_response')
def test_invoke_openai_api_with_file(mock_get_openai_response, mock_get_openai_response_with_attachments):
    mock_get_openai_response_with_attachments.return_value = 'Test response with attachments'
    result = invoke_openai_api('test_question', 'test_file_path', 'gpt-4')
    assert result == 'Test response with attachments'
    assert mock_get_openai_response_with_attachments.called
    assert not mock_get_openai_response.called

@patch('utils.openai_utils.get_openai_response_with_attachments')
@patch('utils.openai_utils.get_openai_response')
def test_invoke_openai_api_without_file(mock_get_openai_response, mock_get_openai_response_with_attachments):
    mock_get_openai_response.return_value = 'Test response without attachments'
    result = invoke_openai_api('test_question', model='gpt-4')
    assert result == 'Test response without attachments'
    assert mock_get_openai_response.called
    assert not mock_get_openai_response_with_attachments.called
