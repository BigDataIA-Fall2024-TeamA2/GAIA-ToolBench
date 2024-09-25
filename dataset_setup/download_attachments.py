import os

import requests
from bs4 import BeautifulSoup

# Base URL for the GitHub repository
base_url = "https://github.com/aymeric-roucher/GAIA/tree/main/data/gaia/validation"
raw_base_url = (
    "https://raw.githubusercontent.com/aymeric-roucher/GAIA/main/data/gaia/validation/"
)

# Directory where you want to save the downloaded files
download_dir = "../resources/file_attachments/"

# Create directory if it doesn't exist
if not os.path.exists(download_dir):
    os.makedirs(download_dir)


# Function to get the file links from the GitHub directory page
def get_file_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to access {url}")
        return []

    print(f"Getting links from {url}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for all file links
    file_links = []
    extensions = [
        ".csv",
        ".xlsx",
        ".png",
        ".pdf",
        ".txt",
        ".mp3",
        ".py",
        ".json",
        ".jsonld",
    ]
    for link in soup.find_all("a", {"class": "Link--primary"}):
        href = link.get("href")
        # if href and any(extension in href for extension in extensions):  # Adjust this if other file types are required
        if href:
            file_name = href.split("/")[-1]
            file_links.append(file_name)

    return file_links


# Function to download files from the raw URL
def download_files(file_links, raw_base_url, download_dir):
    for file_name in file_links:
        file_url = f"{raw_base_url}{file_name}"
        print(f"Downloading {file_url}...")

        response = requests.get(file_url)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded {file_name} successfully.")
        else:
            print(f"Failed to download {file_name}.")


# Get the list of file links
file_links = get_file_links(base_url)

# Download the files
if file_links:
    download_files(file_links, raw_base_url, download_dir)
else:
    print("No files found to download.")
