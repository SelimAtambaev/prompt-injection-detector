"""Layer 2: the ML detector.

Loads the trained classifier and, given an input, emits a single
category-agnostic ``Signal`` whose confidence is the model's attack
probability. It implements the same ``Detector`` interface as the heuristic
layer, so the proxy and the Phase-4 scoring engine treat it uniformly.

The embedder is injected and must match the one used at training time (the
stored ``embedder_name`` is checked, with a warning on mismatch).
"""

from __future__ import annotations

import warnings

import joblib

from app.detection.base import Detector, Signal
from app.detection.ml.embedder import Embedder
from app.detection.ml.train import DEFAULT_MODEL_PATH


class MLDetector(Detector):
    name = "ml_v1"

    def __init__(self, embedder: Embedder, model_path: str = DEFAULT_MODEL_PATH) -> None:
        bundle = joblib.load(model_path)
        self._clf = bundle["classifier"]
        self._threshold: float = bundle["threshold"]
        self._embedder = embedder
        if bundle.get("embedder_name") != embedder.name:
            warnings.warn(
                f"embedder mismatch: model trained with {bundle.get('embedder_name')!r}, "
                f"using {embedder.name!r}",
                stacklevel=2,
            )

    async def detect(self, text: str) -> list[Signal]:
        if not text:
            return []
        X = self._embedder.encode([text])
        prob = float(self._clf.predict_proba(X)[0, 1])
        return [
            Signal(
                category=None,  # binary model: attack-likelihood, not a subtype
                confidence=prob,
                detector=self.name,
                evidence=f"ml attack probability {prob:.2f}",
            )
        ]
