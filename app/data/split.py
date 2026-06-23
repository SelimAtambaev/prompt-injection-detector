"""Leakage-free splitting.

Two properties matter:

1. Group-aware: a whole group (all rows sharing a ``group_id``) goes to exactly
   one split. After dedup each group is usually a single row, but doing the
   split at the group level means the pipeline stays leakage-free even if we
   later keep augmented variants that share a group.

2. Stratified by label: train/val/test each preserve the attack:benign ratio,
   so the validation metric reflects the real distribution.

Deterministic given ``seed`` so runs are reproducible.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict

from app.data.schema import Example


def _group_label(rows: list[Example]) -> int:
    return Counter(r.label for r in rows).most_common(1)[0][0]


def split_examples(
    examples: list[Example],
    train: float = 0.70,
    val: float = 0.15,
    test: float = 0.15,
    seed: int = 42,
) -> list[Example]:
    if abs(train + val + test - 1.0) > 1e-6:
        raise ValueError("train + val + test must sum to 1.0")

    # 1. gather rows into groups
    groups: dict[str, list[Example]] = defaultdict(list)
    for ex in examples:
        groups[ex.group_id or ex.text].append(ex)

    # 2. bucket groups by their label so we can stratify
    by_label: dict[int, list[str]] = defaultdict(list)
    for gid, rows in groups.items():
        by_label[_group_label(rows)].append(gid)

    rng = random.Random(seed)
    assignment: dict[str, str] = {}
    for _label, gids in by_label.items():
        rng.shuffle(gids)
        n = len(gids)
        n_train = int(n * train)
        n_val = int(n * val)
        for i, gid in enumerate(gids):
            if i < n_train:
                assignment[gid] = "train"
            elif i < n_train + n_val:
                assignment[gid] = "val"
            else:
                assignment[gid] = "test"

    # 3. stamp each row with its group's split
    out: list[Example] = []
    for gid, rows in groups.items():
        s = assignment[gid]
        out.extend(ex.model_copy(update={"split": s}) for ex in rows)
    return out
