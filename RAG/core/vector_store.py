import chromadb
from chromadb.config import Settings

client = None
collection = None

def get_collection():
    global client, collection

    if client is None:
        client = chromadb.Client(
            Settings(
                persist_directory="./chroma_db",
                is_persistent=True
            )
        )

    if collection is None:
        collection = client.get_or_create_collection(name="rag_collection")

    return collection


def clear_collection():
    global client, collection

    if client is None:
        get_collection()

    client.delete_collection("rag_collection")
    collection = client.get_or_create_collection(name="rag_collection")