from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
from PIL import Image

# Load the .env file
load_dotenv()

# Load the OpenAI key from the environment
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_KEY)

def check_for_file(input_text):
    words = input_text.split()
    for word in words:
        if os.path.isfile(word):
            return word
    return None

def process_file(file_path):
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == '.json':
        with open(file_path, 'r') as file:
            return json.load(file)
    elif extension == '.csv':
        return pd.read_csv(file_path).to_dict()
    elif extension == '.xml':
        tree = ET.parse(file_path)
        return ET.tostring(tree.getroot(), encoding='unicode')
    elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
        with Image.open(file_path) as img:
            return f"Image size: {img.size}, format: {img.format}"
    else:
        with open(file_path, 'r') as file:
            return file.read()

def create_prompt(user_inputs):
    messages = [
        {"role": "system", "content": "You are a helpful assistant capable of analyzing various file types."}
    ]
    for input_text in user_inputs:
        file_path = check_for_file(input_text)
        if file_path:
            file_content = process_file(file_path)
            messages.append({
                "role": "user",
                "content": f"{input_text}\n\nFile content: {file_content}"
            })
        else:
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
        #"Analyze this JSON file: data.json",
        #"Analyze this XML file: data.xml and answer the following questions:",
        #"What does this CSV contain: data.csv",
        #"Describe this image: image.jpg"
    ]

    messages = create_prompt(user_inputs)
    response = get_response(messages)
    store_and_display_response(response)
