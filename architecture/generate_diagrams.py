from diagrams import Diagram
from diagrams.generic.storage import Storage
from diagrams.programming.language import Python
from diagrams.onprem.database import Postgresql
from diagrams.programming.flowchart import Action
from diagrams.aws.storage import S3
from diagrams.oci.database import BigdataService

def generate_draft_version1():
    with Diagram("Benchmark UI", direction="LR", filename="architecture/diagrams/draft1", outformat="png", show=False) as dia:
        hugging_face_dataset = Storage("GAIA Benchmark - Hugging Face")
        crawler_py = Python("Crawler")
        s3 = S3("S3 Bucket")
        database = Postgresql("PostgreSQL DB")
        streamlit_app = Python("Benchmark UI - Streamlit")
        openai_api = BigdataService("OpenAI API")
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

