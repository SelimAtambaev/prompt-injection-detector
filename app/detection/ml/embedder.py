"""Text embedding for the Layer-2 ML detector.

Two implementations behind one ``Embedder`` interface:

* ``SentenceTransformerEmbedder`` -- the real, recommended path. Dense semantic
  vectors that generalize to paraphrases and unseen phrasings. Pulls torch and
  downloads a model on first use.
* ``HashingEmbedder`` -- a dependency-light fallback (scikit-learn only, no
  torch, no downloads). Bag-of-ngrams feature hashing: weaker on novel wording,
  but fully offline. Used for CI and quick experiments.

Choosing the embedder is the caller's job (dependency injection), which is what
makes train/evaluate/detect testable without the heavy stack.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...
    @property
    def name(self) -> str: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None  # lazy: don't load torch/model until needed

    def _ensure(self):  # type: ignore[no-untyped-def]
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._ensure()
        return np.asarray(model.encode(list(texts), normalize_embeddings=True))

    @property
    def name(self) -> str:
        return f"st:{self.model_name}"


class HashingEmbedder:
    def __init__(self, n_features: int = 2**12) -> None:
        from sklearn.feature_extraction.text import HashingVectorizer

        self.n_features = n_features
        self._vec = HashingVectorizer(
            n_features=n_features, alternate_sign=False, ngram_range=(1, 2)
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._vec.transform(list(texts)).toarray()

    @property
    def name(self) -> str:
        return f"hashing:{self.n_features}"
