from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

from core.embeddings import get_embedding

load_dotenv()

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)


def index_chunks(chunks):

    documents = []

    for i, chunk in enumerate(chunks):

        embedding = get_embedding(chunk["content"])

        documents.append({
            "id": f"{chunk['source']}_{i}",
            "content": chunk["content"],
            "embedding": embedding,
            "source": chunk["source"],
            "type": chunk["type"],
            "section": chunk["section"]
        })

    search_client.upload_documents(documents)