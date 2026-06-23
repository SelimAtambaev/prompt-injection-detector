"""Honest evaluation of the Layer-2 detector.

A detector that blocks everything has perfect recall and is useless; one that
blocks nothing has perfect precision and is useless. So we report the full
picture: precision, recall, F1, ROC-AUC, the confusion matrix, and -- because
over-blocking legitimate users is the real-world cost -- the false-positive
rate explicitly. Latency is reported because this sits on the request hot path.
"""

from __future__ import annotations

import time

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.detection.ml.dataset import load_split
from app.detection.ml.embedder import Embedder
from app.detection.ml.train import DEFAULT_MODEL_PATH


def score(
    embedder: Embedder,
    texts: list[str],
    labels: list[int],
    model_path: str = DEFAULT_MODEL_PATH,
) -> dict[str, object]:
    bundle = joblib.load(model_path)
    clf = bundle["classifier"]
    threshold = bundle["threshold"]

    t0 = time.perf_counter()
    X = embedder.encode(texts)
    proba = clf.predict_proba(X)[:, 1]
    elapsed_ms = (time.perf_counter() - t0) * 1000
    pred = (proba >= threshold).astype(int)

    cm = confusion_matrix(labels, pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "n": len(labels),
        "accuracy": round(float(accuracy_score(labels, pred)), 4),
        "precision": round(float(precision_score(labels, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(labels, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(labels, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(labels, proba)), 4)
        if len(set(labels)) > 1
        else float("nan"),
        "false_positive_rate": round(float(fpr), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "latency_ms_per_example": round(elapsed_ms / max(len(labels), 1), 3),
        "threshold": threshold,
        "embedder": embedder.name,
    }


def report(metrics: dict[str, object]) -> str:
    cm = metrics["confusion_matrix"]
    return (
        f"  examples           {metrics['n']}\n"
        f"  accuracy           {metrics['accuracy']}\n"
        f"  precision          {metrics['precision']}\n"
        f"  recall             {metrics['recall']}\n"
        f"  f1                 {metrics['f1']}\n"
        f"  roc_auc            {metrics['roc_auc']}\n"
        f"  false_positive_rate{metrics['false_positive_rate']:>7}\n"
        f"  confusion          tn={cm['tn']} fp={cm['fp']} fn={cm['fn']} tp={cm['tp']}\n"
        f"  latency/example    {metrics['latency_ms_per_example']} ms\n"
        f"  embedder           {metrics['embedder']}"
    )


def evaluate_from_files(
    embedder: Embedder,
    test_path: str = "data/processed/test.jsonl",
    model_path: str = DEFAULT_MODEL_PATH,
) -> dict[str, object]:
    texts, labels = load_split(test_path)
    metrics = score(embedder, texts, labels, model_path=model_path)
    print(report(metrics))
    return metrics


def main() -> None:
    from app.detection.ml.embedder import SentenceTransformerEmbedder

    evaluate_from_files(SentenceTransformerEmbedder())


if __name__ == "__main__":
    main()
