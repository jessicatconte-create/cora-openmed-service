import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import openmed

app = FastAPI()

OPENMED_SERVICE_TOKEN = os.getenv("OPENMED_SERVICE_TOKEN", "")

DEFAULT_PII_MODEL = "OpenMed/OpenMed-PII-Portuguese-SnowflakeMed-Large-568M-v1"
DEFAULT_DISEASE_MODEL = "OpenMed/OpenMed-NER-DiseaseDetect-SuperClinical-434M"
DEFAULT_PHARMA_MODEL = "OpenMed/OpenMed-NER-PharmaDetect-SuperClinical-434M"
DEFAULT_ANATOMY_MODEL = "OpenMed/OpenMed-NER-AnatomyDetect-SuperClinical-184M"


def _verify_token(authorization: str) -> None:
    if not OPENMED_SERVICE_TOKEN:
        raise HTTPException(status_code=500, detail="Service token not configured")
    if authorization != f"Bearer {OPENMED_SERVICE_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class ExtractRequest(BaseModel):
    text: str
    confidence_threshold: float = 0.5
    model_name: str = DEFAULT_PII_MODEL


class DeidentifyRequest(BaseModel):
    text: str
    method: str = "mask"
    confidence_threshold: float = 0.5
    model_name: str = DEFAULT_PII_MODEL


class AnalyzeRequest(BaseModel):
    text: str
    confidence_threshold: float = 0.3
    model_name: Optional[str] = None


class ClinicalExtractRequest(BaseModel):
    text: str
    confidence_threshold: float = 0.3


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


@app.post("/analyze")
def analyze(req: AnalyzeRequest, authorization: str = Header(...)):
    _verify_token(authorization)
    result = openmed.analyze_text(
        req.text,
        model_name=req.model_name,
        confidence_threshold=req.confidence_threshold,
        output_format="dict",
    )
    return result


@app.post("/clinical/extract")
def clinical_extract(req: ClinicalExtractRequest, authorization: str = Header(...)):
    """Roda os três modelos clínicos em paralelo e retorna entidades consolidadas."""
    _verify_token(authorization)

    threshold = req.confidence_threshold
    text = req.text

    disease_result = openmed.analyze_text(
        text, model_name=DEFAULT_DISEASE_MODEL,
        confidence_threshold=threshold, output_format="dict",
    )
    pharma_result = openmed.analyze_text(
        text, model_name=DEFAULT_PHARMA_MODEL,
        confidence_threshold=threshold, output_format="dict",
    )
    anatomy_result = openmed.analyze_text(
        text, model_name=DEFAULT_ANATOMY_MODEL,
        confidence_threshold=threshold, output_format="dict",
    )

    def get_entities(result):
        if isinstance(result, dict):
            return result.get("entities", [])
        if hasattr(result, "entities"):
            return result.entities
        return []

    return {
        "text": text,
        "conditions": [
            {"text": e["text"], "confidence": e["confidence"], "start": e["start"], "end": e["end"]}
            for e in get_entities(disease_result)
        ],
        "medications": [
            {"text": e["text"], "confidence": e["confidence"], "start": e["start"], "end": e["end"]}
            for e in get_entities(pharma_result)
        ],
        "anatomy": [
            {"text": e["text"], "confidence": e["confidence"], "start": e["start"], "end": e["end"]}
            for e in get_entities(anatomy_result)
        ],
    }
