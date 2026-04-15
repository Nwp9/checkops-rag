from core.vector_store import get_collection
collection = get_collection()

from core.embeddings import get_embedding
import hashlib
from core.vector_store import client
import time

def index_chunks(chunks):

    for chunk in chunks:

        embedding = get_embedding(chunk["content"])
        chunk_id = hashlib.md5((chunk["content"] + str(time.time())).encode()).hexdigest()

        collection.add(
            documents=[chunk["content"]],
            embeddings=[embedding],
            ids=[chunk_id],
            metadatas=[{
                "title": chunk.get("title", ""),
                "source": chunk.get("source", ""),
                "type": chunk.get("type", ""),
                "section": chunk.get("section", "")
            }]
        )

    print("Chunks indexés :", len(chunks))
    print("Total en base :", collection.count())