"""Métricas de recuperación y huella de recursos por ejecución."""
import os
import time
import tracemalloc
from typing import Callable


def recall_at_k(predictions: list[list[str]], truths: list[set[str]]) -> float:
    if not truths or len(predictions) != len(truths):
        raise ValueError("Se requieren etiquetas y predicciones alineadas")
    return sum(bool(set(pred) & expected) for pred, expected in zip(predictions, truths)) / len(truths)


def reciprocal_rank(predictions: list[list[str]], truths: list[set[str]]) -> float:
    if not truths or len(predictions) != len(truths):
        raise ValueError("Se requieren etiquetas y predicciones alineadas")
    scores = []
    for pred, expected in zip(predictions, truths):
        scores.append(next((1 / i for i, item in enumerate(pred, 1) if item in expected), 0.0))
    return sum(scores) / len(scores)


def timed_call(fn: Callable, *args, **kwargs) -> tuple[object, dict]:
    tracemalloc.start()
    start = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, {"latency_ms": round(elapsed * 1000, 3),
                    "python_peak_memory_mb": round(peak / 1024**2, 3),
                    "note": "Memoria Python instrumentada; NO es RAM total, VRAM ni energía."}
