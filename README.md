# Assignment 1

## Setup
- Poetry:
  - Install poetry using this: https://python-poetry.org/docs/#installation
- Once poetry is installed, run `poetry install` and validate the installed packages through `poetry show`
- Create a new `.env` file from `.env.template` and populate it with your tokens & credentials
- Run the command `poetry self add poetry-dotenv-plugin` to install the dotenv plugin for poetry. It will allow running any python without having to reload the shell with the .env variables.

## Components
- architecture
- scraper:
  - Contains the logic required for scraping the dataset and building the database
  - TODO: Database integration
- benchmark-ui:
  - TODO: streamlit app w/ DB and OpenAI integration
