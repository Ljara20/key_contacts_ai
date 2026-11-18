"""Consola local de ingesta, búsqueda exploratoria y modelo TF-IDF persistido."""
import argparse
import json
from pathlib import Path
import pandas as pd
from keycontacts.cleaning.pipeline import run_pipeline
from keycontacts.search.baseline import ContactSearcher
from keycontacts.search.tfidf_model import LocalTfidfModel
from keycontacts.ml.evaluation import timed_call


def main() -> None:
    parser = argparse.ArgumentParser(prog="keycontacts")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Normalizar Excel/CSV")
    ingest.add_argument("file")
    ingest.add_argument("--output", default="data/processed")
    ingest.add_argument("--sheet", default="0")
    search = commands.add_parser("search", help="Buscar con baseline anterior")
    search.add_argument("query")
    search.add_argument("--data", default="data/processed/finance_normalized.csv")
    search.add_argument("--top", type=int, default=3)
    train = commands.add_parser("train-tfidf", help="Construir y guardar el modelo TF-IDF")
    train.add_argument("--data", default="data/processed/finance_normalized.csv")
    train.add_argument("--model", default="models/tfidf_contacts.joblib")
    predict = commands.add_parser("predict-tfidf", help="Consultar el modelo guardado")
    predict.add_argument("query")
    predict.add_argument("--model", default="models/tfidf_contacts.joblib")
    predict.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    if args.command == "ingest":
        sheet = int(args.sheet) if args.sheet.isdigit() else args.sheet
        result = run_pipeline(args.file, args.output, sheet)
    elif args.command == "search":
        frame = pd.read_csv(args.data, dtype="string")
        results, perf = timed_call(ContactSearcher(frame).search, args.query, args.top)
        result = {"candidates": results, "performance": perf}
    elif args.command == "train-tfidf":
        frame = pd.read_csv(args.data, dtype="string")
        model, perf = timed_call(LocalTfidfModel.fit, frame)
        metadata = model.save(args.model)
        result = {"training": metadata, "performance": perf}
    else:
        model = LocalTfidfModel.load(args.model)
        results, perf = timed_call(model.predict, args.query, args.top)
        result = {"candidates": results, "performance": perf}
    if args.command in {"search", "predict-tfidf"}:
        result["warning"] = "Candidatos exploratorios. No se verifican RACI, vigencia ni permisos."
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
