"""Detection engine: runs every detection layer and merges their signals.

The proxy depends on this, not on individual detectors. Layers run cheapest-
first (heuristics, then ML). The ML layer is OPTIONAL at runtime: if the trained
model file is missing or its dependencies (torch) aren't installed, the engine
logs that ML is disabled and proceeds with heuristics only -- the firewall must
never crash just because the model hasn't been trained yet.

(A latency optimization for later: short-circuit and skip the ML layer when the
heuristics already produce a clearly-blocking signal. Kept simple here -- all
layers run, because the score benefits from every signal.)
"""

from __future__ import annotations

import time

import structlog

from app.detection.base import DetectionResult, Detector
from app.detection.heuristics.rules import HeuristicDetector

log = structlog.get_logger()


class DetectionEngine:
    def __init__(self, detectors: list[Detector]) -> None:
        self.detectors = detectors

    @property
    def layer_names(self) -> list[str]:
        return [d.name for d in self.detectors]

    async def detect(self, text: str) -> DetectionResult:
        t0 = time.perf_counter()
        signals = []
        for detector in self.detectors:
            signals.extend(await detector.detect(text))
        return DetectionResult(
            signals=signals,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


def build_default_engine(model_path: str | None = None) -> DetectionEngine:
    detectors: list[Detector] = [HeuristicDetector()]
    try:
        from app.detection.ml.classifier import MLDetector
        from app.detection.ml.embedder import SentenceTransformerEmbedder
        from app.detection.ml.train import DEFAULT_MODEL_PATH

        detectors.append(
            MLDetector(SentenceTransformerEmbedder(), model_path=model_path or DEFAULT_MODEL_PATH)
        )
        log.info("ml_layer_enabled")
    except Exception as exc:  # noqa: BLE001 -- ML is optional; degrade gracefully
        log.warning("ml_layer_disabled", error=str(exc))
    return DetectionEngine(detectors)
