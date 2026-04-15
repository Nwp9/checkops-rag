from core.vector_store import get_collection
collection = get_collection()

from core.embeddings import get_embedding

def search_documents(query, doc_type=None):

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    docs = []

    for i in range(len(results["documents"][0])):

        content = results["documents"][0][i]

        # filtre basique (très important)
        if len(content.strip()) < 10:
            continue

        docs.append({
            "content": content,
            "title": results["metadatas"][0][i].get("title", ""),
            "source": results["metadatas"][0][i].get("source", ""),
            "type": results["metadatas"][0][i].get("type", ""),
            "section": results["metadatas"][0][i].get("section", "")
        })   

    return docs
