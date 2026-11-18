"""Crea una muestra FICTICIA para probar el flujo sin usar datos privados."""
from pathlib import Path
import pandas as pd


def main() -> None:
    output = Path("data/raw/demo_finance.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"WBS": "00123", "Market": "Colombia", "Customer Team": "Finanzas", "Project Description": "Impuestos y facturación Colombia", "FPC Email": "finanzas.ejemplo@example.com", "LM Email": "lider.ejemplo@example.com"},
        {"WBS": "00124", "Market": "Perú", "Customer Team": "Operaciones", "Project Description": "Implementación de redes", "FPC Email": "operaciones.ejemplo@example.com", "LM Email": "lider2.ejemplo@example.com"},
        {"WBS": "00125", "Market": "Colombia", "Customer Team": "Finanzas", "Project Description": "Conciliación y cierre contable", "FPC Email": "contabilidad.ejemplo@example.com", "LM Email": "lider.ejemplo@example.com"},
    ]).to_csv(output, index=False)
    print(output)

if __name__ == "__main__":
    main()
