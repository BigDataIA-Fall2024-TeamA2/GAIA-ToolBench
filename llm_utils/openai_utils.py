import logging
import os
import time
from functools import lru_cache
from typing import Optional

import openai
from openai import OpenAI, OpenAIError
from openai.types.beta import Thread

from utils.s3 import load_file

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
        response = openai_client.beta.vector_stores.files.retrieve(file_id=file_path, vector_store_id=vector_store_id)
    except openai.NotFoundError as nfe:
        file_obj = load_file(file_path)
        message_file = openai_client.files.create(
            file=file_obj,
            purpose="assistants"
        )

        resp = openai_client.beta.vector_stores.files.upload(
            vector_store_id=vector_store_id,
            file=file_obj
        )



def get_openai_response_with_attachments(question: str, model: str, file_path=None):
    """
    Create a prompt with attachment.

    :param question: The user's question
    :param model: The OpenAI model to use
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
        logger.info(f"Assistant {assistant_id} updated with vector store id")

    message_file = openai_client.files.create(
        file=load_file(file_path),
        purpose="assistants"
    )

    thread: Thread = openai_client.beta.threads.create()
    message = openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
        attachments=[{
            "file_id": message_file.id,
            "tools": [{"type": "file_search"}]
        }]
    )
    run = openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
        model=model
    )

    messages = list(openai_client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    return messages[0].content[0].text



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
    openai_client = get_openai_client()
    try:
        completion = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content":
"""You are an intelligent assistant tasked with providing accurate and thoughtful responses based solely on the information in the user's prompt and your existing knowledge base. Your primary goal is to demonstrate strong reasoning abilities by interpreting the user's query, making logical connections, and applying your understanding of the world to generate comprehensive answers. 

Key objectives:
1. Analyze the prompt thoroughly and identify the core questions or issues being raised.
2. Use your internal knowledge to reason through the problem, connecting relevant facts, concepts, and logical inferences.
3. Provide well-explained answers that reflect a deep understanding of the subject, ensuring clarity and precision.
4. Address ambiguities in the prompt by offering logical interpretations or asking for clarifications when needed."""},
                {"role": "user", "content": question},
            ]
        )
    except OpenAIError as e:
        err_msg = e.body["message"]
        logger.error(f"Error while invoking OpenAI API with model: {model} | Error: {err_msg}")
        return f"Error invoking OpenAI API: {err_msg}"
    return completion.choices[0].message.content



def invoke_openai_api(question: str, file_path: Optional[str] = None, model: str ="gpt-4o-mini-2024-07-18") -> str:
    if file_path is not None:
        return get_openai_response_with_attachments(question=question, file_path=file_path, model=model)
    else:
        return get_openai_response(question=question, model=model)


# Example usage:
if __name__ == "__main__":
    ...