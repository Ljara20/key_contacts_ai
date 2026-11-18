"""Contratos mínimos; ausencias no se convierten en valores inventados."""
import re
import pandas as pd

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
FINANCE_CONTACT_FIELDS = ("FPC Email", "Substitute Email", "LM Email")


def validate_finance(df: pd.DataFrame) -> dict:
    cols = set(df.columns)
    emails = [c for c in FINANCE_CONTACT_FIELDS if c in cols]
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_contact_fields": [c for c in FINANCE_CONTACT_FIELDS if c not in cols],
        "available_contact_fields": emails,
        "has_contact_candidate": bool(emails),
        "has_project_description": "Project Description" in cols,
    }


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch(str(value).strip()))
