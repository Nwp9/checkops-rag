from core.vector_store import get_collection
from core.embeddings import get_embedding

collection = get_collection()

def _query_by_type(query_embedding, doc_type, n_results=3):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"type": doc_type},
        include=["documents", "metadatas", "distances"]
    )

    docs = []

    if not results["documents"] or not results["documents"][0]:
        return docs

    for i in range(len(results["documents"][0])):
        content = results["documents"][0][i]
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        if not content or len(content.strip()) < 10:
            continue

        if distance > 1.5:
            continue

        docs.append({
            "content": content,
            "title": metadata.get("title", ""),
            "source": metadata.get("source", ""),
            "type": metadata.get("type", doc_type),
            "section": metadata.get("section", ""),
            "distance": distance
        })

    return docs

def search_documents(query, doc_type=None):

    query_embedding = get_embedding(query)

    # Si un type précis est demandé
    if doc_type:
        docs = _query_by_type(query_embedding, doc_type, n_results=5)
        return sorted(docs, key=lambda d: d["distance"])

    # Recherche hybride séparée
    drawing_docs = _query_by_type(query_embedding, "DRAWING", n_results=3)
    graph_docs = _query_by_type(query_embedding, "GRAPH", n_results=2)
    normal_docs = _query_by_type(query_embedding, "DOC", n_results=3)
    ocr_docs = _query_by_type(query_embedding, "OCR", n_results=2)

    docs = drawing_docs + graph_docs + normal_docs + ocr_docs
   
    # Tri intelligent :
    # 1. DRAWING prioritaire
    # 2. distance faible prioritaire
    docs = sorted(
        docs,
        key=lambda d: (
            d["type"] != "DRAWING",
            d["distance"]
        )
    )

    return docs[:5]
