import os
import time
import hashlib
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from monitoring import (
    rag_requests_total,
    embedding_latency_seconds,
    chunks_indexed_total,
    rag_similarity_score
)


load_dotenv()


# ==============================
# 🔹 Monitoring
# ==============================
def log_metric(name, value):
    with open("metrics.txt", "a") as f:
        f.write(f"{time.time()} | {name} | {value}\n")


# --------------------------------------------------------------------------------------------------------------------------------

# embeddings
from core.embeddings import get_embedding

# retrieval
from core.retrieval import search_documents

# Generation
from core.generation import generate_answer

# OCR
from services.ocr import extract_text_from_image, ingest_ocr_pipeline


# ==============================
# 🔹 RAG
# ==============================
def rag_query(query, doc_type=None):
    rag_requests_total.inc()

    query_clean = query.lower().strip()

    # 🔥 Détection flexible des salutations
    greetings = ["bonjour", "salut", "hello", "hi", "bonsoir"]

    if any(greet in query_clean for greet in greetings):
        return "Bonjour, Je suis votre assistant TechnOps. Posez-moi une question sur la maintenance aéronautique.", []

    docs = search_documents(query, doc_type=doc_type)

    # 🔥 blocage hors périmètre
    if not docs:
        return "❌ Aucun document pertinent n’a été trouvé. Essayez une question liée à un ATA, une procédure, une anomalie ou une opération de maintenance.", []

    answer = generate_answer(query, docs)

    return answer, docs

# ==============================
# 🔹 NO RAG
# ==============================
from core.generation import generate_no_rag_answer

def no_rag_answer(query):
    return generate_no_rag_answer(query)

# ==============================
# 🔹 EVALUATION RAG
# ==============================
def evaluate_rag(answer, docs):
    score = 0

    if docs:
        score += 50

    if "DOC" in answer:
        score += 30

    if len(answer) > 100:
        score += 20

    rag_similarity_score.set(score)

    return score

# ==============================
# 🔹 Incohérences et Score
# ==============================
from core.generation import generate_answer

def detect_inconsistencies(query):
    docs = search_documents(query)
    return generate_answer(query, docs)

def compliance_score(query):
    docs = search_documents(query)
    return generate_answer(query, docs)

# ==============================
# 🔹 PDF
# ==============================
def generate_pdf(query, answer, docs):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("TechnOps Report", styles["Title"]),
        Spacer(1, 10),
        Paragraph(f"<b>Question:</b> {query}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"<b>Answer:</b> {answer}", styles["Normal"]),
        Spacer(1, 20)
    ]

    for d in docs:
        elements.append(
            Paragraph(f"{d['source']} | {d['section']}<br/>{d['content'][:200]}", styles["Normal"])
        )

    doc.build(elements)

    return "report.pdf"



def build_chunks_from_ocr(text):

    # 🔹 Nettoyage simple
    text = text.replace("\r", "\n")
    text = text.strip()

    # 🔹 Split intelligent
    raw_chunks = text.split("\n")

    chunks = []
    buffer = ""

    for line in raw_chunks:

        line = line.strip()

        if not line:
            continue

        buffer += " " + line

        # 🔥 règle de chunk (~400 caractères)
        if len(buffer) > 400:
            chunks.append(buffer.strip())
            buffer = ""

    if buffer:
        chunks.append(buffer.strip())

    return chunks
