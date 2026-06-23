"""Registry of external dataset sources.

Each ``SourceSpec`` records where a dataset lives, how its native columns map
to our schema, its LICENSE, and whether it is quarantined to evaluation only
(e.g. non-commercial licenses) or gated (requires accepting terms on the Hub).

Column names and label encodings vary between datasets and can change; the
loader (collect.py) is defensive and skips a source rather than crashing if its
shape differs. Verify a source's columns in the Hugging Face dataset viewer
before trusting it, and update the spec here -- this registry is meant to be
the single, auditable place that knowledge lives.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.data.schema import LABEL_ATTACK, LABEL_BENIGN
from app.detection.taxonomy import AttackCategory

# Map common source-provided category strings to our taxonomy. Best-effort;
# anything unmapped stays None rather than being forced into a wrong bucket.
_CATEGORY_MAP: dict[str, AttackCategory] = {
    "benign": AttackCategory.BENIGN,
    "jailbreak": AttackCategory.JAILBREAK,
    "instruction_override": AttackCategory.INSTRUCTION_OVERRIDE,
    "direct_injection": AttackCategory.INSTRUCTION_OVERRIDE,
    "role_play": AttackCategory.ROLE_MANIPULATION,
    "role_manipulation": AttackCategory.ROLE_MANIPULATION,
    "data_exfiltration": AttackCategory.DATA_EXFILTRATION,
    "encoding": AttackCategory.ENCODING,
}


@dataclass(frozen=True)
class SourceSpec:
    hf_id: str
    text_col: str = "text"
    label_col: str = "label"
    config: str | None = None
    split: str = "train"
    license: str = "unknown"
    eval_only: bool = False          # quarantine (e.g. non-commercial)
    gated: bool = False              # requires accepting terms / HF login
    category_col: str | None = None
    attack_values: tuple = field(default=(1, "1", True, "injection", "jailbreak", "attack"))
    benign_values: tuple = field(default=(0, "0", False, "benign", "legit", "safe", "legitimate"))

    def to_binary(self, raw: object) -> int | None:
        if raw in self.attack_values:
            return LABEL_ATTACK
        if raw in self.benign_values:
            return LABEL_BENIGN
        return None

    def to_category(self, row: dict) -> AttackCategory | None:
        if not self.category_col:
            return None
        raw = str(row.get(self.category_col, "")).lower().strip()
        return _CATEGORY_MAP.get(raw)


# Order matters only for logging. eval_only sources are excluded from training.
SOURCES: list[SourceSpec] = [
    SourceSpec(hf_id="deepset/prompt-injections", license="apache-2.0"),
    SourceSpec(hf_id="xTRam1/safe-guard-prompt-injection", license="see-card"),
    SourceSpec(
        hf_id="neuralchemy/Prompt-injection-dataset",
        config="core",
        license="see-card",
        category_col="category",
    ),
    SourceSpec(
        hf_id="qualifire/prompt-injections-benchmark",
        license="cc-by-nc-4.0",
        eval_only=True,   # non-commercial -> never in the training mix
        gated=True,       # you must accept terms on the Hub first
    ),
]
