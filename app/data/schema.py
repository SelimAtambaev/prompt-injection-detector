"""Unified schema for the training/eval corpus.

Every external dataset, whatever its native columns, is normalized into a list
of ``Example`` objects. The primary learning target is the BINARY ``label``
(attack vs. benign) -- that is what the public data reliably supports. The
optional ``category`` carries a fine-grained ``AttackCategory`` ONLY when a
source actually provides a mappable category; it is never invented. This honest
split (binary signal from the ML layer, per-category signal from the heuristic
layer) is documented in DATA.md.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.detection.taxonomy import AttackCategory

LABEL_ATTACK = 1
LABEL_BENIGN = 0


class Example(BaseModel):
    text: str                              # original text -- never normalized (see clean.py)
    label: int                             # 1 = attack, 0 = benign
    source: str                            # provenance (HF dataset id)
    category: AttackCategory | None = None  # fine-grained, only when known
    group_id: str | None = None            # for leakage-free, group-aware splitting
    split: str | None = None               # "train" | "val" | "test"
