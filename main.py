import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import openmed

app = FastAPI()

OPENMED_SERVICE_TOKEN = os.getenv("OPENMED_SERVICE_TOKEN", "")
DEFAULT_MODEL = "OpenMed/OpenMed-PII-Portuguese-SnowflakeMed-Large-568M-v1"


def _verify_token(authorization: str) -> None:
    if not OPENMED_SERVICE_TOKEN:
        raise HTTPException(status_code=500, detail="Service token not configured")
    if authorization != f"Bearer {OPENMED_SERVICE_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class ExtractRequest(BaseModel):
    text: str
    confidence_threshold: float = 0.5
    model_name: str = DEFAULT_MODEL


class DeidentifyRequest(BaseModel):
    text: str
    method: str = "mask"
    confidence_threshold: float = 0.5
    model_name: str = DEFAULT_MODEL


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pii/extract")
def extract(req: ExtractRequest, authorization: str = Header(...)):
    _verify_token(authorization)
    result = openmed.extract_pii(
        req.text,
        model_name=req.model_name,
        confidence_threshold=req.confidence_threshold,
    )
    return result.to_dict()


@app.post("/pii/deidentify")
def deidentify(req: DeidentifyRequest, authorization: str = Header(...)):
    _verify_token(authorization)
    result = openmed.deidentify(
        req.text,
        method=req.method,
        model_name=req.model_name,
        confidence_threshold=req.confidence_threshold,
    )
    return result.to_dict()
