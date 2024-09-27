import logging
import os
import time
from functools import lru_cache
from typing import Optional

import openai
import requests
from openai import OpenAI, OpenAIError
from openai.types.beta import Thread
from pandas.io.formats.style_render import refactor_levels
from urllib3 import request

from utils.file_system_utils import load_file, OPENAI_SUPPORTED_FILE_FORMATS, encode_image, LOCAL_CACHE_DIRECTORY

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client():
    if "OPENAI_KEY" not in os.environ:
        raise ValueError("OpenAI Key not found in environment variables")
    return OpenAI(api_key=os.environ["OPENAI_KEY"])


def get_openai_key():
    if "OPENAI_KEY" not in os.environ:
        raise ValueError("OpenAI Key not found in environment variables")
    return os.environ["OPENAI_KEY"]


def get_assistant_id() -> Optional[str]:
    if "OPENAI_ASSISTANT_ID" in os.environ and os.environ["OPENAI_ASSISTANT_ID"]:
        return os.environ["OPENAI_ASSISTANT_ID"]
    raise ValueError("OpenAI Assistant ID not found in environment variables")


def get_vector_store_id() -> Optional[str]:
    if "OPENAI_VECTOR_STORE_ID" in os.environ and os.environ["OPENAI_VECTOR_STORE_ID"]:
        return os.environ["OPENAI_VECTOR_STORE_ID"]
    raise ValueError("OpenAI Vector Store ID not found in environment variables")

def _initial_setup():
    os.makedirs(LOCAL_CACHE_DIRECTORY, exist_ok=True)


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

def _invoke_audio_assistants(model: str, question: str, file_path: str, file_extension: str):
    openai_client = get_openai_client()

    audio_file = open(file_path, "rb")
    transcription = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )

    response = openai_client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI language model. You will be given a question along with transcribed text from an audio file. Your task is to provide an accurate and concise answer to the question based solely on the information provided in the transcribed text."
            },
            {
                "role": "user",
                "content": f"""You will find below the question and the transcribed text from an audio file. Based on the transcribed text, answer the question as accurately as possible.

Question: {question}
Transcribed Audio: {transcription}"""
            }
        ]
    )
    return response.choices[0].message.content


def _invoke_image_assistants(model: str, question: str, file_path: str, file_extension: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_openai_key()}",
    }
    encoded_image = encode_image(file_path)
    file_extension = file_extension.replace(".", "")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{file_extension};base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 600,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.ok:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise ValueError(f"API call to OpenAI Vision API failed with {response.status_code} code and {response.text}")


def _invoke_other_assistants(model: str, question: str, updated_file_path: str, file_extension: str) -> str:

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

    if file_extension not in OPENAI_SUPPORTED_FILE_FORMATS:
        logger.error(
            f"File format {file_extension} is not supported by OpenAI"
        )
        return f"File format {file_extension} is not supported by OpenAI. API call to OpenAI not made."

    message_file = openai_client.files.create(
        file=open(updated_file_path, "rb"),
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
        raise ValueError("File attachment path for a test case cannot be empty")

    file_buffer, updated_file_path = load_file(file_path)
    file_extension = os.path.splitext(updated_file_path)[1]
    match file_extension:
        case ".mp3" | ".mp4" | ".mpeg" | ".mpga" | ".m4a" | ".wav" | "webm":
            return _invoke_audio_assistants(model, question, updated_file_path, file_extension)
        case ".png" | ".jpeg" | ".jpg" | ".webp" | ".gif":
            return _invoke_image_assistants(model, question, updated_file_path, file_extension)
        case _:
            return _invoke_other_assistants(model, question, updated_file_path, file_extension)


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
    model: str = "gpt-4o-2024-05-13",
) -> str:
    # Create directories if not present
    _initial_setup()
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
