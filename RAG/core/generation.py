from openai import AzureOpenAI
import os
from dotenv import load_dotenv

import time
from monitoring import llm_latency_seconds
from services.logger import get_logger

logger = get_logger()

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

chat_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# Réponse avec RAG
def generate_answer(query, context_docs):

    start_time = time.time()

    try:
        context = "\n\n".join([
            f"[{doc.get('type','DOC')}]\n{doc['content']}"
            for doc in context_docs
        ])


        #context = "\n\n".join([doc["content"] for doc in context_docs])

        response = client.chat.completions.create(
            model=chat_model,
            messages=[
                {
                    "role": "system",

                    "content": (
                        "You are an INDUSTRIAL TECHNICAL ASSISTANT specialized in mechanical, electrical and electronic systems.\n\n"

                        "You MUST follow these rules:\n"
                        "1. Answer ONLY using the provided context.\n"
                        "2. If the answer is NOT explicitly in the context, say:\n"
                        "'I don't have enough information in the provided documents.'\n"
                        "3. Do NOT use prior knowledge.\n"
                        "4. Do NOT guess.\n"
                        "5. If context is weak or unrelated, refuse.\n\n"

                        "RESPONSE STYLE:\n"
                        "- Use technical vocabulary\n"
                        "- Be precise and structured\n"
                        "- If relevant, explain components, functions, and interactions\n"
                        "- Think like an engineer analyzing a system\n"
                        "- Prefer bullet points when useful\n"
                        "If the context contains DRAWING data:\n"
                        "- Prioritize information extracted from drawings\n"
                        "- Interpret components, structure, and function\n"
                        "- Use drawing analysis to infer system behavior\n\n"

                        "STRUCTURE YOUR ANSWER AS:\n"
                        "1. Identification of the system\n"
                        "2. Description of main components\n"
                        "3. Functional explanation (how it works)\n"
                        "4. Technical summary\n\n"

                        "At the end of the answer, add a SOURCES section.\n"
                        "For each source used, mention its type and title if available.\n"
                        "Example:\n"
                        "SOURCES:\n"
                        "- DRAWING: test_plan.png\n"
                        "- DOC: maintenance_manual.pdf\n\n"

                        "If the context contains GRAPH data:\n"
                        "- Use it to describe connections between components\n"
                        "- Prioritize relationships and structure over raw description\n"
                        "- Explain how components are linked together\n\n"
                    )
                                  
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion:\n{query}"
                }
            ]
        )

        latency = time.time() - start_time
        llm_latency_seconds.observe(latency)

        logger.info(
            "LLM generation completed",
            extra={
                "extra_data": {
                    "latency": latency,
                    "nb_tokens_context": len(context),
                }
            }
        )

        return response.choices[0].message.content
    
    except Exception as e:
        print("ERREUR LLM :", str(e))
        return f"Erreur LLM : {str(e)}"

    # except Exception as e:

    #     latency = time.time() - start_time

    #     logger.error(
    #         "LLM generation failed",
    #         extra={
    #             "extra_data": {
    #                 "error": str(e),
    #                 "latency": latency
    #             }
    #         }
    #     )

    #     raise e
    
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