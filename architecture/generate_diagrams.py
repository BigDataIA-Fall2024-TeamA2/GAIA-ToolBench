from diagrams import Diagram
from diagrams.generic.storage import Storage
from diagrams.programming.language import Python
from diagrams.onprem.database import Postgresql
from diagrams.programming.flowchart import Action
from diagrams.aws.storage import S3
from diagrams.oci.database import BigdataService
from diagrams.custom import Custom

# Define custom classes for your icons
class StreamlitIcon(Custom):
    def __init__(self, label):
        super().__init__(label=label, icon_path="/Users/pranalichipkar/Documents/Pranali/BigData-Assignments/Assignment1/architecture/streamlit-logo-primary-colormark-darktext.png")  # Path to your custom Streamlit icon

class OpenAIIcon(Custom):
    def __init__(self, label):
        super().__init__(label=label, icon_path="/Users/pranalichipkar/Documents/Pranali/BigData-Assignments/Assignment1/architecture/OpenAI_Logo.svg.png")  # Path to your custom OpenAI icon

def generate_draft_version1():
    with Diagram("Benchmark UI", direction="LR", filename="diagrams/draft2", outformat="png", show=False) as dia:
        hugging_face_dataset = Storage("GAIA Benchmark - Hugging Face")
        crawler_py = Python("Crawler")
        s3 = S3("S3 Bucket")
        database = Postgresql("PostgreSQL DB")
        
       


        # Custom icons for Streamlit and OpenAI
        streamlit_app = Custom("Benchmark UI - Streamlit", icon_path="/Users/pranalichipkar/Documents/Pranali/BigData-Assignments/Assignment1/architecture/streamlit-logo-primary-colormark-darktext.png")
        openai_api = Custom("OpenAI API", icon_path="/Users/pranalichipkar/Documents/Pranali/BigData-Assignments/Assignment1/architecture/OpenAI_Logo.svg.png")


        
        page1, page2, page3, page4 = [
            Action("Landing Page"),
            Action("Basic Response"),
            Action("CoT Response"),
            Action("Summary")
        ]

        hugging_face_dataset >> crawler_py
        crawler_py >> database
        crawler_py >> s3

        database << streamlit_app
        streamlit_app >> [
            page1, page2, page3, page4
        ]
        [page2, page3] >> openai_api

    return dia


if __name__ == '__main__':
    # Generating the first sketch draft version
    generate_draft_version1()
