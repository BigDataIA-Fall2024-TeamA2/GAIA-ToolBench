FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG POSTGRES_CONN_STRING
ENV POSTGRES_CONN_STRING=$POSTGRES_CONN_STRING

ARG AWS_ACCESS_KEY_ID
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID

ARG AWS_SECRET_ACCESS_KEY
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

ARG AWS_REGION
ENV AWS_REGION=$AWS_REGION

ARG AWS_S3_BUCKET
ENV AWS_S3_BUCKET=$AWS_S3_BUCKET

ARG OPENAI_KEY
ENV OPENAI_KEY=$OPENAI_KEY

ARG OPENAI_ASSISTANT_ID
ENV OPENAI_ASSISTANT_ID=$OPENAI_ASSISTANT_ID

ARG OPENAI_VECTOR_STORE_ID
ENV OPENAI_VECTOR_STORE_ID=$OPENAI_VECTOR_STORE_ID

COPY models /app/models

COPY utils /app/utils

COPY pages /app/pages

COPY app.py /app/app.py

COPY manage.py /app/manage.py

COPY requirements-docker.txt /app/requirements.txt

RUN pip3 install --no-cache-dir -r /app/requirements-docker.txt

EXPOSE 8080

ENTRYPOINT [ "streamlit", "run", "/app/app.py", "--server.port=8080", "--server.address=0.0.0.0" ]