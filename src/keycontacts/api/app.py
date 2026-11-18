"""API opcional, sin lógica de negocio embebida."""
import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from keycontacts.search.baseline import ContactSearcher

app = FastAPI(title="Key Contacts AI - MVP local", version="0.1.0")

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(request: SearchRequest):
    path = Path(os.getenv("CONTACTS_DATA", "data/processed/finance_normalized.csv"))
    if not path.exists():
        raise HTTPException(status_code=503, detail="Ejecute primero el pipeline de ingesta")
    frame = pd.read_csv(path, dtype="string")
    try:
        candidates = ContactSearcher(frame).search(request.query, request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"query": request.query, "candidates": candidates,
            "warning": "Candidatos orientativos: sin RACI validado ni autorización por rol; no usar en producción."}
