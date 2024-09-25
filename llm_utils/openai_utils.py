import logging
from functools import lru_cache
from idlelib.format import get_indent
from opcode import opname
from typing import Optional

from openai import OpenAI, AssistantEventHandler, api_key, OpenAIError
import os
import time

from openai.types.beta import Thread

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_openai_client():
    if "OPENAI_KEY" not in os.environ:
        raise ValueError("OpenAI Key not found in environment variables")
    return OpenAI(api_key=os.environ["OPENAI_KEY"])


def get_assistant_id() -> Optional[str]:
    if "OPENAI_ASSISTANT_ID" in os.environ and os.environ["OPENAI_ASSISTANT_ID"]:
        return os.environ["ASSISTANT_ID"]
    raise ValueError("OpenAI Assistant ID not found in environment variables")


def get_vector_store_id() -> Optional[str]:
    if "OPENAI_VECTOR_STORE_ID" in os.environ and os.environ["OPENAI_VECTOR_STORE_ID"]:
        return os.environ["OPENAI_VECTOR_STORE_ID"]
    raise ValueError("OpenAI Vector Store ID not found in environment variables")


def wait_on_run(openai_client: OpenAI, run, thread):
    """
    Wait for the Assistants run to finish and return the response.
    :param openai_client:
    :param run:
    :param thread:
    :return:
    """
    while run.status == "queued" or run.status == 'in_progress':
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)

    if run.status in ["requires_action", "cancelling", "cancelled", "failed", "incomplete", "expired"]:
        raise ValueError("OpenAI Assistant computing chat completion failed with status: " + str(run.status))

    return run


def upload_file_to_vectorstore(openai_client: OpenAI, vector_store_id: str, file_path: str) -> str:
    """
    Upload the file to the vector store and return the id of the uploaded file.
    :param openai_client:
    :param vector_store_id:
    :param file_path:
    :return:
    """
    try:
        response = openai_client.beta.vector_stores.files.retrieve(file_path)



def get_openai_response_with_attachments(question, model="gpt-4o-mini-2024-07-18", file_path=None):
    """
    Create a prompt with attachment.

    :param question: The user's question
    :param file_path: Optional path to a file to attach
    :return: Tuple of (assistant_id, thread_id)
    """
    if not file_path:
        logger.error("File path cannot be empty")
        return "Missing attachment file path"

    openai_client = get_openai_client()
    assistant_id = get_assistant_id()
    vector_store_id = get_vector_store_id()

    assistant = openai_client.beta.assistants.retrieve(assistant_id=assistant_id)
    if vector_store_id not in assistant.tool_resources.file_search.vector_store_ids:
        assistant = openai_client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id],
                }
            }
        )

    thread: Thread = openai_client.beta.threads.create()
    message = openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    completed_run = wait_on_run(openai_client, run, thread)
    messages = openai_client.beta.threads.messages.list(thread_id=thread.id)

    for message in messages.data:
        if message.role == "assistant":
            return message.content[0].text.value





    # Create a Vector Store
    vector_store = client.beta.vector_stores.create(name="Financial Statements")

    # Upload file to the Vector Store
    with open(file_path, "rb") as file:
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=[file]
        )

    # Update Assistant with Vector Store
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # Create a Thread with File Attachment
    message_file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
    thread = client.beta.threads.create(
        messages=[{
            "role": "user",
            "content": question,
            "attachments": [
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ],
        }]
    )

    return assistant.id, thread.id


def get_openai_response(question: str, model: str) -> str:
    """
    This function sends a question to the specified OpenAI model and returns the response.
    The system message sets the context that the AI assistant is being benchmarked for performance and should answer quickly and accurately.

    Args:
        question (str): The user's question to be answered by the AI assistant.
        model (str): The OpenAI model to use for the response.

    Returns:
        str: The response from the AI assistant as a string.
    """
    client = get_openai_client()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an AI assistant being benchmarked for performance. Return just answer without any "
                                              "explanation as accurately as possible"},
                {"role": "user", "content": question},
            ]
        )
    except OpenAIError as e:
        err_msg = e.body["message"]
        logger.error(f"Error while invoking OpenAI API with model: {model} | Error: {err_msg}")
        return f"Error invoking OpenAI API: {err_msg}"
    return completion.choices[0].message.content



def invoke_openai_api(question: str, file_path: Optional[str] = None) -> str:
    ...

# Example usage:
if __name__ == "__main__":
    question = "Analyze this financial report."
    file_path = "financial_report1.pdf"  # Replace with the actual path to your file

    assistant_id, thread_id = create_prompt(question, file_path)
    response = get_response(assistant_id, thread_id)
    print("\nFinal Response:")
    print(response)
