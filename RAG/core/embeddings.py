from openai import AzureOpenAI
import os
import time
from dotenv import load_dotenv

from monitoring import embedding_latency_seconds

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")


def get_embedding(text):
    start = time.time()

    embedding = client.embeddings.create(
        model=embedding_model,
        input=text
    ).data[0].embedding

    embedding_latency_seconds.observe(time.time() - start)

    return embedding