from app.core.config import AZURE_VISION_KEY, AZURE_VISION_ENDPOINT

import requests


def describe_image(image_url):

    url = f"{AZURE_VISION_ENDPOINT}/computervision/imageanalysis:analyze?api-version=2024-02-01"

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "url": image_url
    }

    params = {
        "features": "caption"
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    result = response.json()

    try:
        caption = result["captionResult"]["text"]

        return {
            "status": "success",
            "description": caption,
            "source": "azure_vision"
        }

    except Exception:
        return {
            "status": "error",
            "message": "Impossible d'analyser l'image",
            "details": result
        }


def extract_text_from_image(image_url):

    url = f"{AZURE_VISION_ENDPOINT}/computervision/imageanalysis:analyze?api-version=2024-02-01"

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "url": image_url
    }

    params = {
        "features": "read"
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    result = response.json()

    try:
        blocks = result["readResult"]["blocks"]
        extracted_text = []

        for block in blocks:
            for line in block["lines"]:
                extracted_text.append(line["text"])

        full_text = "\n".join(extracted_text)

        return {
            "status": "success",
            "text": full_text,
            "source": "azure_vision_ocr"
        }

    except Exception:
        return {
            "status": "error",
            "message": "Impossible d'extraire le texte",
            "details": result
        }