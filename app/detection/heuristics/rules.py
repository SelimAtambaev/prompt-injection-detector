"""Layer 1: heuristic / signature detection.

Fast (sub-millisecond), fully explainable, HIGH-PRECISION / LOW-RECALL by
design. This layer catches known attack phrasings cheaply on every request. It
deliberately does NOT try to catch novel attacks -- that is the job of the
Phase 3 ML layer. Confidence values are hand-set priors, not learned
probabilities; the Phase 4 scoring engine is responsible for calibration.
"""

from __future__ import annotations

import re

from app.detection.base import Detector, Signal
from app.detection.taxonomy import AttackCategory as AC

# (compiled pattern, category, confidence, human-readable evidence label)
_RULES: list[tuple[re.Pattern[str], AC, float, str]] = [
    (
        re.compile(r"\bignore (all |the )?(previous|prior|above)\b", re.I),
        AC.INSTRUCTION_OVERRIDE, 0.85, "override phrase: 'ignore previous'",
    ),
    (
        re.compile(r"\bdisregard (all |your )?(instructions|rules|guidelines)\b", re.I),
        AC.INSTRUCTION_OVERRIDE, 0.80, "override phrase: 'disregard instructions'",
    ),
    (
        re.compile(r"\b(you are (now|no longer)|act as|pretend to be)\b", re.I),
        AC.ROLE_MANIPULATION, 0.60, "role reassignment phrase",
    ),
    (
        re.compile(r"\b(DAN|do anything now|developer mode|jailbreak)\b", re.I),
        AC.JAILBREAK, 0.75, "known jailbreak keyword",
    ),
    (
        re.compile(
            r"\b(system prompt|initial prompt|your instructions)\b.{0,40}"
            r"\b(reveal|show|print|repeat|display)\b",
            re.I,
        ),
        AC.DATA_EXFILTRATION, 0.80, "system-prompt extraction attempt",
    ),
    (
        re.compile(
            r"\b(reveal|show|print|repeat|display)\b.{0,40}"
            r"\b(system prompt|initial prompt|your instructions)\b",
            re.I,
        ),
        AC.DATA_EXFILTRATION, 0.80, "system-prompt extraction attempt",
    ),
    (
        # long base64-like blob -- low confidence: legitimate text has these too
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        AC.ENCODING, 0.50, "long base64-like token",
    ),
    (
        # invisible / zero-width / bidi-control unicode used to hide instructions
        re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]"),
        AC.HIDDEN_PROMPT, 0.70, "invisible/zero-width unicode characters",
    ),
]


class HeuristicDetector(Detector):
    name = "heuristic_v1"

    async def detect(self, text: str) -> list[Signal]:
        if not text:
            return []
        signals: list[Signal] = []
        for pattern, category, confidence, evidence in _RULES:
            if pattern.search(text):
                signals.append(
                    Signal(
                        category=category,
                        confidence=confidence,
                        detector=self.name,
                        evidence=evidence,
                    )
                )
        return signals
