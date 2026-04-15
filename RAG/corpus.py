import os
import hashlib
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from monitoring import rag_latency_seconds, retrieval_docs_count, rag_errors_total

from monitoring import (
    rag_requests_total,
    rag_latency_seconds,
    rag_similarity_score,
    rag_errors_total
)
import time

load_dotenv()

# Logger
from services.logger import get_logger
logger = get_logger()

# ==============================
#  Monitoring
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
#  RAG
# ==============================
def rag_query(query, doc_type=None):
    start_time = time.time()

    logger.info(
        "RAG query received",
        extra={
            "extra_data": {
                "query": query,
                "doc_type": doc_type
            }
        }
    )

    try:
        rag_requests_total.inc()     
        query_clean = query.lower().strip()

        greetings = ["bonjour", "salut", "hello", "hi", "bonsoir"]

        if any(greet in query_clean for greet in greetings):
            response = "Bonjour, Je suis votre assistant CheckOps. Posez-moi une question sur la maintenance aéronautique."

            latency = time.time() - start_time

            logger.info(
                "Greeting detected",
                extra={
                    "extra_data": {
                        "query": query,
                        "latency": latency,
                        "nb_docs": 0
                    }
                }
            )

            rag_latency_seconds.observe(latency)

            return response, []

        docs = search_documents(query, doc_type=doc_type)

        retrieval_docs_count.observe(len(docs))

        # Filtre de pertinence
        if docs:
            avg_length = sum(len(d["content"]) for d in docs) / len(docs)

            if avg_length < 20:
                return "Je ne trouve pas d'information pertinente dans les documents.", []

        if not docs:
            response = "❌ Aucun document pertinent n’a été trouvé. Essayez une question liée à un ATA, une procédure, une anomalie ou une opération de maintenance."

            latency = time.time() - start_time

            logger.warning(
                "No documents found",
                extra={
                    "extra_data": {
                        "query": query,
                        "latency": latency,
                        "nb_docs": 0
                    }
                }
            )

            rag_latency_seconds.observe(latency)

            return response, []

        answer = generate_answer(query, docs)

        latency = time.time() - start_time

        logger.info(
            "RAG query completed",
            extra={
                "extra_data": {
                    "query": query,
                    "latency": latency,
                    "nb_docs": len(docs)
                }
            }
        )

        rag_latency_seconds.observe(latency)

        return answer, docs

    except Exception as e:

        latency = time.time() - start_time
        rag_errors_total.inc()

        logger.error(
            "RAG query failed",
            extra={
                "extra_data": {
                    "query": query,
                    "error": str(e),
                    "latency": latency
                }
            }
        )

        return "❌ Une erreur interne est survenue. Veuillez réessayer.", []
# ==============================
#  NO RAG
# ==============================
from core.generation import generate_no_rag_answer

def no_rag_answer(query):
    return generate_no_rag_answer(query)

# ==============================
#  EVALUATION RAG
# ==============================

import numpy as np

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def evaluate_rag(query, docs):
    
    if not docs:
        rag_similarity_score.set(0)
        return 0

    # embedding de la question
    query_embedding = get_embedding(query)

    scores = []

    for doc in docs:
        doc_embedding = get_embedding(doc["content"])
        sim = cosine_similarity(query_embedding, doc_embedding)
        scores.append(sim)

    # moyenne des similarités
    avg_score = sum(scores) / len(scores)

    # normalisation 0 → 100
    final_score = round(avg_score * 100, 2)

    rag_similarity_score.set(final_score)

    return final_score

# ==============================
# Incohérences et Score
# ==============================
from core.generation import generate_answer

def detect_inconsistencies(query):
    docs = search_documents(query)
    return generate_answer(query, docs)

def compliance_score(query):
    docs = search_documents(query)
    return generate_answer(query, docs)

# ==============================
#  PDF
# ==============================

def generate_pdf(query, answer, docs):

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    elements = []

    # Titre
    elements.append(Paragraph("CheckOps-Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Question
    elements.append(Paragraph("<b>Question :</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(query, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Réponse
    elements.append(Paragraph("<b>Réponse :</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(answer, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Sources
    if docs:
        elements.append(Paragraph("<b>Sources :</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        for d in docs:
            content = d["content"][:300].replace("\n", "<br/>")
            elements.append(Paragraph(f"<b>{d.get('title','Document')}</b>", styles["Normal"]))
            elements.append(Paragraph(content, styles["Normal"]))
            elements.append(Spacer(1, 10))

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

from PyPDF2 import PdfReader
import docx

def extract_text_from_file(file_path, file_type):

    text = ""

    if file_type == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file_type == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    return text



import os

def ingest_document(file_path, file_type):

    text = extract_text_from_file(file_path, file_type)

    chunks = build_chunks_from_ocr(text)

    # Nom du fichier propre
    filename = os.path.basename(file_path).lower().strip()

    # format attendu par index_chunks
    formatted_chunks = []

    for i, chunk in enumerate(chunks):
        formatted_chunks.append({
            "title": filename,         
            "content": chunk,
            "source": filename,
            "type": "DOC",
            "section": f"part_{i}"
        })

    return formatted_chunks
