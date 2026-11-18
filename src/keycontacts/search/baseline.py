"""Recuperación TF-IDF local; candidatos, no asignaciones verificadas."""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DESCRIPTION_COLUMNS = ("Project Description", "Customer Team", "Market", "Market Unit", "System")
CONTACT_COLUMNS = ("FPC Email", "Substitute Email", "LM Email")


class ContactSearcher:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame.reset_index(drop=True).copy()
        fields = [c for c in DESCRIPTION_COLUMNS if c in self.frame.columns]
        if not fields:
            raise ValueError("No existen campos descriptivos para construir índice TF-IDF")
        texts = self.frame[fields].fillna("").astype(str).agg(" ".join, axis=1)
        if not texts.str.strip().any():
            raise ValueError("No hay descripciones para indexar")
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode", min_df=1)
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not query.strip():
            return []
        sim = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        # Deduplicar correos (un contacto puede aparecer en varios proyectos).
        results = []
        seen = set()
        for index in sim.argsort()[::-1]:
            if len(results) >= top_k or float(sim[index]) <= 0:
                break
            row = self.frame.iloc[int(index)]
            for col in CONTACT_COLUMNS:
                if col not in row or pd.isna(row[col]):
                    continue
                address = str(row[col]).strip().lower()
                if not address or address in seen:
                    continue
                seen.add(address)
                results.append({"contact": address, "source_field": col,
                                "score": round(float(sim[index]), 5),
                                "project_description": str(row.get("Project Description", "")),
                                "verified_responsibility": False})
                if len(results) >= top_k:
                    break
        return results
