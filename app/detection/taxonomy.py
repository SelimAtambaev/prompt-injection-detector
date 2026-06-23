"""Canonical threat taxonomy for the Prompt Injection Detector.

This module is the single source of truth for attack categories. Every
detector, dataset label, log entry, risk score, and dashboard metric MUST
reference these IDs. Do not introduce category strings anywhere else in the
codebase -- doing so causes silent label drift between training data, runtime
detection, and reporting.

Versioned: bump TAXONOMY_VERSION on any change to category membership so that
historical logs and trained models remain interpretable.

See THREAT_MODEL.md for definitions, example signatures, and detection
difficulty for each category.
"""

from __future__ import annotations

from enum import Enum

TAXONOMY_VERSION = "1.0.0"


class AttackCategory(str, Enum):
    """The classes a piece of input can be labeled as.

    Inheriting from ``str`` makes members JSON-serializable and directly
    comparable to plain strings (useful for log parsing and dataset I/O).
    """

    BENIGN = "benign"
    INSTRUCTION_OVERRIDE = "instruction_override"
    JAILBREAK = "jailbreak"
    ROLE_MANIPULATION = "role_manipulation"
    DATA_EXFILTRATION = "data_exfiltration"
    ENCODING = "encoding"
    HIDDEN_PROMPT = "hidden_prompt"
    MULTI_TURN = "multi_turn"

    @classmethod
    def attack_categories(cls) -> list["AttackCategory"]:
        """All categories except BENIGN (i.e. the positive/attack classes)."""
        return [c for c in cls if c is not cls.BENIGN]


class InjectionVector(str, Enum):
    """How the malicious content reaches the model.

    DIRECT   -- in the user's own input.
    INDIRECT -- via content the model ingests (documents, web pages, RAG
                chunks, tool output). Harder to defend; acknowledged but only
                partially covered in v1.
    """

    DIRECT = "direct"
    INDIRECT = "indirect"


# Default per-category severity weights, in [0, 1]. These are *priors* used by
# the Phase 4 risk-scoring engine and are expected to be tuned empirically.
# They are NOT detection confidences -- they express "how bad is it if this
# category is truly present".
DEFAULT_SEVERITY: dict[AttackCategory, float] = {
    AttackCategory.BENIGN: 0.0,
    AttackCategory.INSTRUCTION_OVERRIDE: 0.9,
    AttackCategory.JAILBREAK: 0.9,
    AttackCategory.ROLE_MANIPULATION: 0.7,
    AttackCategory.DATA_EXFILTRATION: 1.0,
    AttackCategory.ENCODING: 0.6,
    AttackCategory.HIDDEN_PROMPT: 0.8,
    AttackCategory.MULTI_TURN: 0.8,
}
