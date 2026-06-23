"""Risk scoring engine.

Turns the set of signals from all detection layers into one risk score in
[0, 1]. The model:

* Each signal contributes ``confidence x weight``. For heuristic signals the
  weight is the category's severity (from the taxonomy) -- a high-confidence
  hit on a low-severity category (e.g. a base64 blob) should not score as high
  as the same confidence on data exfiltration. For the ML signal (category
  None) the weight is ``risk_ml_weight``.
* Contributions combine via NOISY-OR: ``1 - prod(1 - c_i)``. This treats each
  detector as independent evidence, so corroborating signals compound (two
  weak-ish hits raise the score more than either alone) while a single strong
  hit still dominates. It also stays bounded in [0, 1].

This is an interpretable, *tunable heuristic* risk score -- not a calibrated
probability. Weights and thresholds are meant to be tuned against the
validation set; the defaults are sane starting points, documented in SCORING.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings
from app.detection.base import DetectionResult, Signal
from app.detection.taxonomy import DEFAULT_SEVERITY


@dataclass
class RiskResult:
    score: float
    contributions: list[dict] = field(default_factory=list)
    top_signal: Signal | None = None


def _weight(sig: Signal, ml_weight: float) -> float:
    if sig.category is None:  # category-agnostic ML signal
        return ml_weight
    return DEFAULT_SEVERITY.get(sig.category, 0.5)


def score_result(result: DetectionResult, ml_weight: float | None = None) -> RiskResult:
    ml_w = settings.risk_ml_weight if ml_weight is None else ml_weight
    if not result.signals:
        return RiskResult(score=0.0)

    contributions: list[dict] = []
    top_signal: Signal | None = None
    top_contribution = -1.0
    product = 1.0

    for sig in result.signals:
        weight = _weight(sig, ml_w)
        contribution = min(1.0, max(0.0, sig.confidence * weight))
        contributions.append(
            {
                "detector": sig.detector,
                "category": sig.category.value if sig.category else None,
                "confidence": round(sig.confidence, 3),
                "weight": round(weight, 3),
                "contribution": round(contribution, 3),
            }
        )
        product *= 1.0 - contribution
        if contribution > top_contribution:
            top_contribution = contribution
            top_signal = sig

    return RiskResult(
        score=round(1.0 - product, 4),
        contributions=contributions,
        top_signal=top_signal,
    )
