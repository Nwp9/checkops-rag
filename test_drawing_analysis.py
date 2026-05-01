import sys
import os

# 👇 on ajoute le dossier RAG au path Python
sys.path.append(os.path.join(os.path.dirname(__file__), "RAG"))

from services.drawing_analysis import analyze_industrial_drawing

image_path = "test_plan.png"

result = analyze_industrial_drawing(image_path)

print("\n===== ANALYSE DU PLAN =====\n")
print(result)

from services.drawing_analysis import build_chunks_from_drawing_analysis

chunks = build_chunks_from_drawing_analysis(result, "test_plan.png")

print("\n===== CHUNKS =====\n")
print(chunks)

from core.indexing import index_chunks

nb_chunks = index_chunks(chunks)

print("\n===== INDEXATION =====\n")
print(f"{nb_chunks} chunk(s) indexé(s)")

from core.retrieval import search_documents

query = "Quel est le rôle de la pièce dans ce plan ?"

docs = search_documents(query)

print("\n===== RETRIEVAL =====\n")
for d in docs:
    print(d["type"], "-", d["content"][:200])

from corpus import rag_query

answer, sources = rag_query("Quel est le rôle de la pièce dans ce plan ?")

print("\n===== REPONSE RAG =====\n")
print(answer)

print("\n===== SOURCES =====\n")
for s in sources:
    print(s["type"], "-", s["source"])