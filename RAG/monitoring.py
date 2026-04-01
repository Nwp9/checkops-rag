from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# 🔥 registre unique
registry = CollectorRegistry()

rag_requests_total = Counter(
    "rag_requests_total",
    "Nombre total de requêtes RAG effectuées",
    registry=registry
)

embedding_latency_seconds = Histogram(
    "embedding_latency_seconds",
    "Temps de génération des embeddings",
    registry=registry
)

chunks_indexed_total = Counter(
    "chunks_indexed_total",
    "Nombre total de chunks envoyés à Azure Search",
    registry=registry
)

rag_similarity_score = Gauge(
    "rag_similarity_score",
    "Score de similarité de la réponse RAG",
    registry=registry
)