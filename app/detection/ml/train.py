"""Train the Layer-2 binary detector.

Pipeline: embed text -> fit Logistic Regression -> persist the classifier plus
metadata. Logistic Regression is the deliberate default: fast, gives calibrated
probabilities (which the Phase-4 risk engine needs), and is interpretable.
``class_weight="balanced"`` keeps the minority class from being ignored.

The embedder is NOT pickled (you don't want a torch model inside a joblib
file); only its name is stored, for a sanity check at load time. The caller
supplies a matching embedder when loading -- see classifier.py.
"""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression

from app.detection.ml.dataset import load_split
from app.detection.ml.embedder import Embedder, SentenceTransformerEmbedder

DEFAULT_MODEL_PATH = "models/ml_classifier.joblib"


def fit(
    embedder: Embedder,
    texts: list[str],
    labels: list[int],
    out_path: str = DEFAULT_MODEL_PATH,
    threshold: float = 0.5,
) -> str:
    X = embedder.encode(texts)
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X, labels)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"classifier": clf, "embedder_name": embedder.name, "threshold": threshold},
        out_path,
    )
    return out_path


def train_from_files(
    embedder: Embedder,
    train_path: str = "data/processed/train.jsonl",
    out_path: str = DEFAULT_MODEL_PATH,
) -> str:
    texts, labels = load_split(train_path)
    path = fit(embedder, texts, labels, out_path=out_path)
    print(f"trained on {len(texts)} examples -> {path}")
    return path


def main() -> None:
    train_from_files(SentenceTransformerEmbedder())


if __name__ == "__main__":
    main()
