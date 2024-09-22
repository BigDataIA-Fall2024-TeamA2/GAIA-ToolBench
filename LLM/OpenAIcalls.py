from openai import OpenAI
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Load the OpenAI key from the environment
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_KEY)

def create_prompt(user_inputs):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    for input_text in user_inputs:
        messages.append({"role": "user", "content": input_text})
    return messages

def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def store_and_display_response(response, filename='responses.txt'):
    """Store and display the assistant's response."""
    if response:
        with open(filename, 'a') as f:
            f.write(response + "\n")
        print("Response stored:\n", response)
    else:
        print("No response to store.")

# Example usage
if __name__ == "__main__":
    user_inputs = [
        "Who won the World Series in 2020?",
        "Where was it played?"
    ]

    messages = create_prompt(user_inputs)
    response = get_response(messages)
    store_and_display_response(response)
