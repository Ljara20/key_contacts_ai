"""Interfaz de consola para ejecutar módulos localmente."""
import argparse
import json
from pathlib import Path
import pandas as pd
from keycontacts.cleaning.pipeline import run_pipeline
from keycontacts.search.baseline import ContactSearcher
from keycontacts.ml.evaluation import timed_call


def main() -> None:
    parser = argparse.ArgumentParser(prog="keycontacts")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Normalizar Excel/CSV y emitir informe")
    ingest.add_argument("file")
    ingest.add_argument("--output", default="data/processed")
    ingest.add_argument("--sheet", default="0", help="Nombre o índice de hoja Excel")
    search = commands.add_parser("search", help="Buscar candidatos TF-IDF")
    search.add_argument("query")
    search.add_argument("--data", default="data/processed/finance_normalized.csv")
    search.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    if args.command == "ingest":
        sheet = int(args.sheet) if args.sheet.isdigit() else args.sheet
        result = run_pipeline(args.file, args.output, sheet)
    else:
        frame = pd.read_csv(args.data, dtype="string")
        results, perf = timed_call(ContactSearcher(frame).search, args.query, args.top)
        result = {"candidates": results, "performance": perf,
                  "warning": "No verifica RACI, vigencia ni permisos: prueba técnica únicamente."}
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
