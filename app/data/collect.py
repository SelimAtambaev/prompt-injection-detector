"""Collection: pull each registered source and normalize it to ``Example``s.

Requires the optional ``data`` extra (``pip install -e ".[data]"``) for the
``datasets`` library, and network access to the Hugging Face Hub. A source that
fails to load (gated, renamed columns, offline) is logged and skipped rather
than aborting the whole run -- partial corpora are better than no corpus.
"""

from __future__ import annotations

import structlog

from app.data.schema import Example
from app.data.sources import SOURCES, SourceSpec

log = structlog.get_logger()


def load_source(spec: SourceSpec) -> list[Example]:
    from datasets import load_dataset  # imported lazily so offline tests don't need it

    ds = load_dataset(spec.hf_id, spec.config, split=spec.split)
    out: list[Example] = []
    for row in ds:
        text = row.get(spec.text_col)
        label = spec.to_binary(row.get(spec.label_col))
        if text is None or label is None:
            continue
        out.append(
            Example(
                text=str(text),
                label=label,
                source=spec.hf_id,
                category=spec.to_category(row),
            )
        )
    return out


def collect(specs: list[SourceSpec] | None = None) -> list[Example]:
    """Collect all training sources (eval_only sources are excluded)."""
    specs = specs or [s for s in SOURCES if not s.eval_only]
    examples: list[Example] = []
    for spec in specs:
        try:
            rows = load_source(spec)
            examples.extend(rows)
            log.info("source_loaded", source=spec.hf_id, n=len(rows), license=spec.license)
        except Exception as exc:  # noqa: BLE001 -- intentionally broad; skip & continue
            log.warning("source_skipped", source=spec.hf_id, error=str(exc), gated=spec.gated)
    return examples
