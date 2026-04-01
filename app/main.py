from fastapi import FastAPI
from pydantic import BaseModel

from app.core.dispatcher import analyze

app = FastAPI()


class RequestModel(BaseModel):
    type: str
    task: str
    data: str


@app.post("/analyze")
def analyze_endpoint(request: RequestModel):
    return analyze(request)