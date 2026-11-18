"""Modelo local TF-IDF persistente: recuperación exploratoria de candidatos.

No hace inferencias de responsabilidad RACI, no verifica estado ni permisos.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from keycontacts.search.baseline import DESCRIPTION_COLUMNS, CONTACT_COLUMNS
from keycontacts.validation.schema import valid_email

MODEL_VERSION = "tfidf-v1"


@dataclass
class LocalTfidfModel:
    """Índice construido una vez y consultable sin reentrenarlo."""
    frame: pd.DataFrame
    vectorizer: TfidfVectorizer
    matrix: object
    source_hash: str

    @classmethod
    def fit(cls, frame: pd.DataFrame) -> "LocalTfidfModel":
        if frame.empty:
            raise ValueError("No hay registros para indexar")
        fields = [c for c in DESCRIPTION_COLUMNS if c in frame.columns]
        if not fields:
            raise ValueError("Faltan campos descriptivos")
        clean = frame.reset_index(drop=True).copy()
        texts = clean[fields].fillna("").astype(str).agg(" ".join, axis=1)
        if not texts.str.strip().any():
            raise ValueError("Todos los textos de referencia están vacíos")
        vectorizer = TfidfVectorizer(
            strip_accents="unicode", lowercase=True,
            ngram_range=(1, 2), min_df=1, norm="l2", dtype=np.float32,
        )
        matrix = vectorizer.fit_transform(texts)
        fingerprint = hashlib.sha256(
            texts.to_json(orient="values", force_ascii=False).encode("utf-8")
        ).hexdigest()
        return cls(clean, vectorizer, matrix, fingerprint)

    def predict(self, query: str, top_k: int = 3) -> list[dict]:
        if top_k < 1:
            raise ValueError("top_k debe ser >= 1")
        if not query or not query.strip():
            return []
        query_vector = self.vectorizer.transform([query])
        if query_vector.nnz == 0:
            return []  # Ninguna palabra de la consulta existe en el vocabulario
        similarities = (self.matrix @ query_vector.T).toarray().ravel()
        # Orden estable ante empates para que el benchmark sea reproducible.
        ranked = np.argsort(-similarities, kind="stable")
        result: list[dict] = []
        seen: set[str] = set()
        for idx in ranked:
            score = float(similarities[idx])
            if score <= 0 or len(result) >= top_k:
                break
            row = self.frame.iloc[int(idx)]
            for col in CONTACT_COLUMNS:
                if col not in self.frame or pd.isna(row[col]):
                    continue
                contact = str(row[col]).strip().lower()
                if not valid_email(contact) or contact in seen:
                    continue
                seen.add(contact)
                result.append({
                    "contact": contact,
                    "source_field": col,
                    "score": round(score, 6),
                    "project_description": "" if pd.isna(row.get("Project Description")) else str(row.get("Project Description", "")),
                    "source_row": int(idx),
                    "verified_responsibility": False,
                })
                if len(result) >= top_k:
                    break
        return result

    def save(self, target: str | Path) -> dict:
        """Guardar SOLO en ubicación local confiable. joblib usa pickle."""
        dest = Path(target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, dest, compress=3)
        metadata = {
            "version": MODEL_VERSION,
            "rows": len(self.frame),
            "features": len(self.vectorizer.vocabulary_),
            "source_hash": self.source_hash,
            "model_size_bytes": dest.stat().st_size,
            "model_path": str(dest),
            "warning": "Índice exploratorio, no certifica responsable ni autorización.",
        }
        dest.with_suffix(".json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return metadata

    @classmethod
    def load(cls, path: str | Path) -> "LocalTfidfModel":
        """Nunca cargar archivos .joblib de terceros o ubicaciones no confiables."""
        model = joblib.load(path)
        if not isinstance(model, cls):
            raise ValueError("El archivo no contiene un índice TF-IDF compatible")
        return model
