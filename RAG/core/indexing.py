from core.vector_store import get_collection
collection = get_collection()

from core.embeddings import get_embedding
import hashlib
import time

from monitoring import chunks_indexed_total

def index_chunks(chunks):

    for chunk in chunks:

        embedding = get_embedding(chunk["content"])
        chunk_id = hashlib.md5(
            (
                chunk.get("source", "") +
                chunk.get("section", "") +
                chunk["content"]
            ).encode("utf-8")
        ).hexdigest()

        # chunk_id = hashlib.md5((chunk["content"] + str(time.time())).encode()).hexdigest()

        collection.upsert(
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

        chunks_indexed_total.inc()

    return len(chunks)