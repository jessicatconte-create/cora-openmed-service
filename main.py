from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import httpx
import hashlib
import os

app = FastAPI()

OPENMED_BASE_URL = "http://localhost:8080"
OPENMED_SERVICE_TOKEN = os.getenv("OPENMED_SERVICE_TOKEN", "")


def _verify_token(authorization: str) -> None:
    if not OPENMED_SERVICE_TOKEN:
        raise HTTPException(status_code=500, detail="Service token not configured")
    if authorization != f"Bearer {OPENMED_SERVICE_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class ExtractRequest(BaseModel):
    text: str
    confidence_threshold: float = 0.5
    model_name: str = "OpenMed/OpenMed-PII-Portuguese-SnowflakeMed-Large-568M-v1"


class DeidentifyRequest(BaseModel):
    text: str
    method: str = "mask"
    confidence_threshold: float = 0.5
    model_name: str = "OpenMed/OpenMed-PII-Portuguese-SnowflakeMed-Large-568M-v1"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pii/extract")
async def extract(req: ExtractRequest, authorization: str = Header(...)):
    _verify_token(authorization)
    payload = {
        "text": req.text,
        "model_name": req.model_name,
        "confidence_threshold": req.confidence_threshold,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OPENMED_BASE_URL}/pii/extract", json=payload)
    r.raise_for_status()
    return r.json()


@app.post("/pii/deidentify")
async def deidentify(req: DeidentifyRequest, authorization: str = Header(...)):
    _verify_token(authorization)
    payload = {
        "text": req.text,
        "method": req.method,
        "model_name": req.model_name,
        "confidence_threshold": req.confidence_threshold,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OPENMED_BASE_URL}/pii/deidentify", json=payload)
    r.raise_for_status()
    return r.json()
