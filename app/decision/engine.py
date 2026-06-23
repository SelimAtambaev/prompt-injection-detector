"""Decision engine.

Maps the risk score (from the scoring engine) to an action. Thresholds live in
config so they can be tuned without code changes. This replaces the Phase-1
placeholder that thresholded raw max-confidence; the proxy now feeds it the
combined risk score.
"""

from __future__ import annotations

from enum import Enum

from app.core.config import settings


class Verdict(str, Enum):
    ALLOW = "allow"   # forward to the LLM
    FLAG = "flag"     # forward, but record as suspicious
    BLOCK = "block"   # do not forward


def decide(risk_score: float) -> Verdict:
    if risk_score >= settings.block_threshold:
        return Verdict.BLOCK
    if risk_score >= settings.flag_threshold:
        return Verdict.FLAG
    return Verdict.ALLOW
