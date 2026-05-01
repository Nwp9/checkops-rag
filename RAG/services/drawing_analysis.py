import os
import base64
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except:
#     pass
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

vision_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_industrial_drawing(image_path):
    """
    Analyse simple d’un dessin industriel.
    Pour l’instant, ce module ne touche pas au RAG existant.
    """

    image_base64 = encode_image(image_path)

    response = client.chat.completions.create(
        model=vision_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant expert en analyse de dessins industriels. "
                    "Tu dois analyser des plans mécaniques, électriques ou électroniques. "
                    "Décris uniquement ce que tu observes dans l'image."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyse ce dessin industriel. "
                            "Identifie le type de schéma, les composants visibles, "
                            "les annotations, les symboles, les connexions et les éventuelles informations techniques."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

def build_chunks_from_drawing_analysis(analysis_text, filename):
    return [
        {
            "title": filename,
            "content": analysis_text,
            "source": filename,
            "type": "DRAWING",
            "section": "industrial_drawing_analysis"
        }
    ]