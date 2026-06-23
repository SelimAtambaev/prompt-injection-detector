"""Load the processed JSONL splits produced by app.data.build."""

from __future__ import annotations

from pathlib import Path

from app.data.schema import Example


def load_split(path: str | Path) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = Example.model_validate_json(line)
            texts.append(ex.text)
            labels.append(ex.label)
    return texts, labels
