from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
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

def search_documents(query, doc_type=None):

    query_vector = get_embedding(query)

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=3,
        fields="embedding"
    )

    filter_query = None
    if doc_type:
        filter_query = f"type eq '{doc_type}'"

    results = search_client.search(
        search_text="",
        vector_queries=[vector_query],
        filter=filter_query
    )

    docs = []
    for result in results:
        docs.append({
            "content": result["content"],
            "source": result.get("source", ""),
            "type": result.get("type", ""),
            "section": result.get("section", "")
        })

    return docs