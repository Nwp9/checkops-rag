from app.services.text_service import process_text
from app.services.image_service import describe_image, extract_text_from_image


def analyze(input_data):

    content = input_data.data

    # Détection automatique
    if isinstance(content, str) and content.startswith("http"):
        data_type = "image"
    else:
        data_type = "text"

    if data_type == "text":
        return process_text(input_data.task, content)

    elif data_type == "image":

        if input_data.task == "describe":
            return describe_image(content)

        elif input_data.task == "ocr":
            return extract_text_from_image(content)

        return {
            "status": "error",
            "message": f"Tâche image '{input_data.task}' non supportée"
        }

    return {
        "status": "error",
        "message": f"Type '{data_type}' non supporté"
    }