"""Build the processed corpus: collect -> clean -> split -> write JSONL.

Run from the project root after installing the data extra:

    pip install -e ".[data]"
    python -m app.data.build

Writes data/processed/{train,val,test}.jsonl and prints a summary table with
class balance per split, so you can eyeball that the split is sane before any
training happens.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.data.clean import clean
from app.data.collect import collect
from app.data.schema import Example
from app.data.split import split_examples


def write_jsonl(rows: list[Example], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ex in rows:
            f.write(ex.model_dump_json() + "\n")


def summarize(rows: list[Example]) -> str:
    by_split: dict[str, Counter] = {}
    for ex in rows:
        by_split.setdefault(ex.split or "?", Counter())[ex.label] += 1
    lines = ["split    total  attack  benign"]
    for name in ("train", "val", "test"):
        c = by_split.get(name, Counter())
        total = c[0] + c[1]
        lines.append(f"{name:<7} {total:>6} {c[1]:>7} {c[0]:>7}")
    return "\n".join(lines)


def main(out_dir: str = "data/processed") -> None:
    raw = collect()
    print(f"collected: {len(raw)} examples")
    cleaned = clean(raw)
    print(f"after clean/dedup: {len(cleaned)} examples (removed {len(raw) - len(cleaned)})")
    split = split_examples(cleaned)

    out = Path(out_dir)
    for name in ("train", "val", "test"):
        rows = [ex for ex in split if ex.split == name]
        write_jsonl(rows, out / f"{name}.jsonl")

    print(summarize(split))
    print(f"written to {out.resolve()}")


if __name__ == "__main__":
    main()
