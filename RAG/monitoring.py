from prometheus_client import Counter, Histogram, Gauge, REGISTRY

def get_or_create_metric(metric_type, name, documentation):
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return metric_type(name, documentation)

rag_requests_total = get_or_create_metric(
    Counter,
    "rag_requests_total",
    "Nombre total de requêtes RAG effectuées"
)

embedding_latency_seconds = get_or_create_metric(
    Histogram,
    "embedding_latency_seconds",
    "Temps de génération des embeddings"
)

chunks_indexed_total = get_or_create_metric(
    Counter,
    "chunks_indexed_total",
    "Nombre total de chunks envoyés à Azure Search"
)

rag_similarity_score = get_or_create_metric(
    Gauge,
    "rag_similarity_score",
    "Score de similarité de la réponse RAG"
)

rag_latency_seconds = get_or_create_metric(
    Histogram,
    "rag_latency_seconds",
    "Temps total RAG"
)

llm_latency_seconds = get_or_create_metric(
    Histogram,
    "llm_latency_seconds",
    "Temps LLM"
)

retrieval_docs_count = get_or_create_metric(
    Histogram,
    "retrieval_docs_count",
    "Nombre de documents"
)

rag_errors_total = get_or_create_metric(
    Counter,
    "rag_errors_total",
    "Nombre d'erreurs RAG"
)