"""Normalización conservadora con trazabilidad y cuarentena."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from keycontacts.ingestion.readers import read_table
from keycontacts.validation.schema import validate_finance, FINANCE_CONTACT_FIELDS, valid_email


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    clean.columns = [str(c).strip() for c in clean.columns]
    if clean.columns.duplicated().any():
        raise ValueError("Columnas duplicadas después de normalizar encabezados")
    for col in clean.columns:
        clean[col] = clean[col].astype("string").str.strip().replace("", pd.NA)
    for col in FINANCE_CONTACT_FIELDS:
        if col in clean:
            clean[col] = clean[col].str.lower()
    return clean


def run_pipeline(source: str | Path, output: str | Path, sheet: str | int = 0) -> dict:
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    df = read_table(source, sheet)
    meta = validate_finance(df)
    clean = normalize(df)
    # Nunca eliminar filas duplicadas silenciosamente: registrar y conservar.
    dup = clean.duplicated(keep=False)
    errors = pd.Series("", index=clean.index, dtype="string")
    for col in FINANCE_CONTACT_FIELDS:
        if col in clean:
            bad = clean[col].notna() & ~clean[col].fillna("").map(valid_email)
            errors.loc[bad] = errors.loc[bad] + f"invalid_{col};"
    # Una fila sin correo puede seguir aportando contexto: no descartarla por defecto.
    exceptions = clean.loc[errors.ne("")].copy()
    if not exceptions.empty:
        exceptions["_validation_errors"] = errors.loc[exceptions.index]
    clean.to_csv(output / "finance_normalized.csv", index=False, encoding="utf-8-sig")
    exceptions.to_csv(output / "finance_review.csv", index=False, encoding="utf-8-sig")
    report = {
        "source_name": source.name,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": meta,
        "duplicate_rows_to_review": int(dup.sum()),
        "rows_with_invalid_email": len(exceptions),
        "null_counts": {k: int(v) for k, v in clean.isna().sum().items()},
        "outputs": ["finance_normalized.csv", "finance_review.csv"],
        "notes": "No se infieren responsables RACI, ni se imputan correos o estados.",
    }
    (output / "quality_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
