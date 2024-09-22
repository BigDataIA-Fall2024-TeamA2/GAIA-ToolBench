from openai import OpenAI, AssistantEventHandler
#from typing_extensions import override
from dotenv import load_dotenv
import os
import time
# Load the .env file
load_dotenv()

# Load the OpenAI key from the environment
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_KEY)

def create_prompt(question, file_path=None):
    """
    Create a prompt with or without file attachment.

    :param question: The user's question
    :param file_path: Optional path to a file to attach
    :return: Tuple of (assistant_id, thread_id)
    """
    # Create an Assistant with File Search capability
    assistant = client.beta.assistants.create(
        name="Financial Analyst Assistant",
        instructions="You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
        model="gpt-4-1106-preview",
        tools=[{"type": "file_search"}],
    )

    if file_path:
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
    else:
        # Create a Thread without File Attachment
        thread = client.beta.threads.create(
            messages=[{
                "role": "user",
                "content": question,
            }]
        )

    return assistant.id, thread.id

def get_response(assistant_id, thread_id):
    """
    Get the response from the assistant.

    :param assistant_id: The ID of the assistant
    :param thread_id: The ID of the thread
    :return: The assistant's response
    """
    # Create a run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Poll for the run to complete
    while run.status not in ["completed", "failed"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        print(f"Run status: {run.status}")
        time.sleep(5)  # Wait for 1 second before checking again

    if run.status == "failed":
        return f"Run failed with error: {run.last_error}"

    # Retrieve messages after the run is completed
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    # Get the last assistant message
    for message in messages.data:
        if message.role == "assistant":
            return message.content[0].text.value

    return "No response from assistant."

# Example usage:
if __name__ == "__main__":
    question = "Analyze this financial report."
    file_path = "financial_report1.pdf"  # Replace with the actual path to your file

    assistant_id, thread_id = create_prompt(question, file_path)
    response = get_response(assistant_id, thread_id)
    print("\nFinal Response:")
    print(response)
