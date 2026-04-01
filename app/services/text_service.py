from app.core.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_DEPLOYMENT
)

import requests


def generate_text(prompt):

    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }

    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["choices"][0]["message"]["content"]


def process_text(task, text):

    if task == "summarize":
        prompt = f"Résume ce texte en une phrase : {text}"

    elif task == "explain":
        prompt = f"Explique simplement : {text}"

    else:
        return {
            "status": "error",
            "message": f"Tâche '{task}' non supportée"
        }

    result = generate_text(prompt)

    return {
        "status": "success",
        "task": task,
        "input": text,
        "output": result,
        "source": "azure_openai"
    }