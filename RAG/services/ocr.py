from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
import os

vision_client = ImageAnalysisClient(
    endpoint=os.getenv("AZURE_VISION_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_VISION_KEY"))
)

def test_ocr(image_path):

    with open(image_path, "rb") as f:
        image_data = f.read()

    result = vision_client.analyze(
        image_data=image_data,
        visual_features=[VisualFeatures.READ]
    )

    text = ""

    if result.read:
        for block in result.read.blocks:
            for line in block.lines:
                text += line.text + "\n"

    return text

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

# Indexation du OCR

def ingest_ocr_pipeline(image_path):

    # 1. OCR
    text = test_ocr(image_path)

    # 2. Chunking (ta fonction étape 3)
    raw_chunks = build_chunks_from_ocr(text)

    # 3. Structuration (compatible avec index_chunks)
    chunks = []

    for i, chunk in enumerate(raw_chunks):

        chunks.append({
            "content": chunk,
            "source": "OCR_UPLOAD",
            "type": "OCR",
            "section": f"OCR_{i}"
        })

    # 4. Indexation 

    from core.indexing import index_chunks
    from monitoring import chunks_indexed_total

    index_chunks(chunks)
    chunks_indexed_total.inc(len(chunks))
    return len(chunks)

def extract_text_from_image(image_path):
    return test_ocr(image_path)