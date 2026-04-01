from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

chat_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# Réponse avec RAG
def generate_answer(query, context_docs):

    context = "\n\n".join([doc["content"] for doc in context_docs])

    response = client.chat.completions.create(
        model=chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are TechnOps Assistant, an aviation maintenance expert with more than 10 years "
                    "of hands-on experience in aircraft systems. You are a certified aerospace engineer "
                    "specialized in airframe and powerplant (cellule et moteurs). You master all major "
                    "aircraft mechanical systems including hydraulics, flight controls, landing gear, "
                    "fuel systems, pneumatics, bleeds, pressurization, environmental control systems, "
                    "engine operation, lubrication, ignition, FADEC logic, and structural assemblies. "
                    "You understand ATA chapters, maintenance procedures, troubleshooting logic, "
                    "technical documentation, and operational constraints. "
                    "You answer ONLY using the provided context. If the context does not contain the "
                    "information, you do not invent anything."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{query}"
            }
        ]
    )

    return response.choices[0].message.content

# Réponse sans RAG 
def generate_no_rag_answer(query):

    response = client.chat.completions.create(
        model=chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You provide general, high-level information about aviation and aircraft. "
                    "You are NOT a specialist and you do NOT provide technical maintenance expertise. "
                    "Your answers remain broad, educational, and non-technical."
                )
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    return response.choices[0].message.content