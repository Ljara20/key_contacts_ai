"""Lectura segura y explícita de fuentes locales Excel/CSV."""
from pathlib import Path
import pandas as pd

SUPPORTED = {".csv", ".xlsx"}


def read_table(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Archivo inexistente: {source}")
    if source.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Formato no soportado: {source.suffix}")
    if source.suffix.lower() == ".csv":
        # Encodings comunes en exportaciones corporativas.
        last_error = None
        for encoding in ("utf-8-sig", "cp1252"):
            try:
                return pd.read_csv(source, dtype="string", keep_default_na=False,
                                   encoding=encoding, sep=None, engine="python")
            except UnicodeError as exc:
                last_error = exc
        raise ValueError(f"No se pudo decodificar CSV: {last_error}")
    return pd.read_excel(source, sheet_name=sheet, dtype="string", keep_default_na=False)
