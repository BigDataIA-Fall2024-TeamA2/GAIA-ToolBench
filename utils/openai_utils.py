import logging
import os
import time
from functools import lru_cache
from typing import Optional

import openai
from openai import OpenAI, OpenAIError
from openai.types.beta import Thread

from utils.file_system_utils import load_file, OPENAI_SUPPORTED_FILE_FORMATS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client():
    if "OPENAI_KEY" not in os.environ:
        raise ValueError("OpenAI Key not found in environment variables")
    return OpenAI(api_key=os.environ["OPENAI_KEY"])


def get_assistant_id() -> Optional[str]:
    if "OPENAI_ASSISTANT_ID" in os.environ and os.environ["OPENAI_ASSISTANT_ID"]:
        return os.environ["OPENAI_ASSISTANT_ID"]
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
    while run.status == "queued" or run.status == "in_progress":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)

    if run.status in [
        "requires_action",
        "cancelling",
        "cancelled",
        "failed",
        "incomplete",
        "expired",
    ]:
        raise ValueError(
            "OpenAI Assistant computing chat completion failed with status: "
            + str(run.status)
        )

    return run


def upload_file_to_vectorstore(
    openai_client: OpenAI, vector_store_id: str, file_path: str
) -> str:
    """
    Upload the file to the vector store and return the id of the uploaded file.
    :param openai_client:
    :param vector_store_id:
    :param file_path:
    :return:
    """
    try:
        response = openai_client.beta.vector_stores.files.retrieve(
            file_id=file_path, vector_store_id=vector_store_id
        )
    except openai.NotFoundError as nfe:
        file_obj = load_file(file_path)
        message_file = openai_client.files.create(file=file_obj, purpose="assistants")

        resp = openai_client.beta.vector_stores.files.upload(
            vector_store_id=vector_store_id, file=file_obj
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
            },
        )
        logger.info(f"Assistant {assistant_id} updated with vector store id")

    # Download the file from S3, verify the file extension is usable with OpenAI, and upload to OpenAI
    file_buffer, relevant_file_name = load_file(file_path)
    if os.path.splitext(relevant_file_name)[1] not in OPENAI_SUPPORTED_FILE_FORMATS:
        logger.error(
            f"File format {os.path.splitext(relevant_file_name)} is not supported by OpenAI"
        )
        return f"File format {os.path.splitext(relevant_file_name)[1]} is not supported by OpenAI. API call to OpenAI not made."

    message_file = openai_client.files.create(
        file=open(relevant_file_name, "rb"),
        purpose="assistants",
    )

    thread: Thread = openai_client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": question,
                "attachments": [
                    {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )
    # message = openai_client.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="user",
    #     content=question,
    #     attachments=[{"file_id": message_file.id, "tools": [{"type": "file_search"}]}],
    # )
    run = openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_id, model=model
    )

    messages = list(
        openai_client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    )

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []

    for idx, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(
            annotation.text, f"[{idx}]"
        )
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = openai_client.files.retrieve(file_citation.file_id)
            citations.append(f"[{idx}] {cited_file.filename}")

    final_message = message_content.value + "\n\n " + "\n".join(citations)
    return final_message


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
                {
                    "role": "system",
                    "content": """You are an assistant designed to provide clear and accurate answers based on the information in the user's prompt. Use your knowledge to reason through the query and offer concise, relevant, and well-explained responses.""",
                },
                {"role": "user", "content": question},
            ],
        )
    except OpenAIError as e:
        err_msg = e.body["message"]
        logger.error(
            f"Error while invoking OpenAI API with model: {model} | Error: {err_msg}"
        )
        return f"Error invoking OpenAI API: {err_msg}"
    return completion.choices[0].message.content


def invoke_openai_api(
    question: str,
    file_path: Optional[str] = None,
    model: str = "gpt-4o-mini-2024-07-18",
) -> str:
    if file_path is not None:
        return get_openai_response_with_attachments(
            question=question, file_path=file_path, model=model
        )
    else:
        return get_openai_response(question=question, model=model)


# Example usage:
if __name__ == "__main__":
    question3 = """An office held a Secret Santa gift exchange where each of its twelve employees was assigned one other employee in the group to present with a gift. Each employee filled out a profile including three likes or hobbies. On the day of the gift exchange, only eleven gifts were given, each one specific to one of the recipient's interests. Based on the information in the document, who did not give a gift?
    """
    fp3 = "cffe0e32-c9a6-4c52-9877-78ceb4aaa9fb.docx"

    invoke_openai_api(question3, fp3)
