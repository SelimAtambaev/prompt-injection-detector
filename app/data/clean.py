"""Cleaning and deduplication.

The critical idea: we compute a NORMALIZED KEY for dedup/grouping, but we keep
the ORIGINAL text as the training input. Normalization (NFKC + lowercase +
whitespace collapse) is great for finding duplicates, but applying it to the
training text would erase the very signals some attacks rely on -- zero-width
characters, casing tricks, spacing. So normalization touches the key only.

Deduplication removes near-identical prompts (same normalized key). Duplicate
prompts that survive into both train and test are the #1 cause of inflated,
dishonest accuracy numbers; removing them is non-negotiable.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from app.data.schema import Example

_WHITESPACE = re.compile(r"\s+")


def normalized_key(text: str) -> str:
    """Canonical form used ONLY for dedup/grouping -- never for training."""
    t = unicodedata.normalize("NFKC", text).casefold().strip()
    return _WHITESPACE.sub(" ", t)


def group_id(text: str) -> str:
    """Stable id shared by near-identical texts, for group-aware splitting."""
    return hashlib.sha1(normalized_key(text).encode("utf-8")).hexdigest()[:16]


def clean(
    examples: Iterable[Example],
    min_chars: int = 1,
    max_chars: int = 20_000,
) -> list[Example]:
    seen: set[str] = set()
    out: list[Example] = []
    for ex in examples:
        text = (ex.text or "").strip()
        if not (min_chars <= len(text) <= max_chars):
            continue
        gid = group_id(text)
        if gid in seen:
            continue  # near-duplicate of something already kept
        seen.add(gid)
        out.append(ex.model_copy(update={"text": text, "group_id": gid}))
    return out
