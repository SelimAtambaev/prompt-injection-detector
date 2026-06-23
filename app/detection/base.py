"""The detection contract.

Every detection layer (heuristics now; embeddings/transformer later) implements
``Detector`` and returns a list of ``Signal`` objects. The proxy and the scoring
engine depend only on this interface, never on a concrete detector -- this is the
Strategy pattern, and it is what lets later phases add layers without touching
the proxy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.detection.taxonomy import AttackCategory


class Signal(BaseModel):
    """One piece of evidence that an attack category may be present.

    ``category`` is the fine-grained attack type when the detector knows it
    (the heuristic layer). It is ``None`` for category-agnostic detectors -- the
    Layer-2 ML model is a binary attack/benign classifier, so it reports an
    attack *likelihood* without claiming a specific subtype.
    """

    category: AttackCategory | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    detector: str          # which detector produced this (provenance)
    evidence: str          # human-readable reason (explainability)


class DetectionResult(BaseModel):
    """The aggregate output of running one or more detectors on an input."""

    signals: list[Signal] = Field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def max_confidence(self) -> float:
        return max((s.confidence for s in self.signals), default=0.0)


class Detector(ABC):
    """Base class for all detection layers."""

    name: str = "base"

    @abstractmethod
    async def detect(self, text: str) -> list[Signal]:
        """Return zero or more signals for the given text.

        Implementations must be robust to arbitrary input and should not raise
        on malformed or adversarial text -- a detector that crashes is a
        denial-of-service vector.
        """
        raise NotImplementedError
