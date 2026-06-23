# Data (Phase 2)

How the training/evaluation corpus is built, and the decisions behind it. The
pipeline lives in `app/data/` and is run with:

```bash
pip install -e ".[data]"     # adds `datasets` + `pandas`
python -m app.data.build     # writes data/processed/{train,val,test}.jsonl
```

## The central decision: binary ML target, per-category heuristics

The public datasets are overwhelmingly **binary** (attack vs. benign), not
labeled across our eight fine-grained categories. Rather than fabricate labels,
the design is:

- **ML layer (Phase 3): binary** — "how attack-like is this input?" This is what
  the data supports and what the literature does.
- **Heuristic layer (Phase 1): per-category** — already supplies which category
  fired and why.

The taxonomy remains the reporting/logging schema; the ML model contributes a
calibrated binary signal that the Phase-4 risk engine combines with the
heuristic signals. Where a source *does* carry a mappable category (e.g.
`neuralchemy`), we keep it in `Example.category` for an optional multi-class
head later — but it is never invented.

## Sources

| Dataset | Shape | License | Role |
|---------|-------|---------|------|
| `deepset/prompt-injections` | binary, EN/DE | Apache-2.0 | core training (clean license) |
| `xTRam1/safe-guard-prompt-injection` | ~7k safe / 3k injection | see card | training |
| `neuralchemy/Prompt-injection-dataset` (`core`) | binary + category/severity | see card | training + category enrichment |
| `qualifire/prompt-injections-benchmark` | jailbreak/benign | CC-BY-NC-4.0 (gated) | **eval only** — quarantined |

Licensing is enforced in code: `qualifire` is marked `eval_only=True` so it can
never enter the training mix (its non-commercial license would contaminate a
portfolio you may want to describe as freely usable). Gated sources require
accepting terms on the Hub and a `huggingface-cli login` first; if you haven't,
the loader logs and skips them rather than crashing.

Always verify a source's columns in the Hugging Face dataset viewer before
trusting it — column names and label encodings drift. The single place that
knowledge lives is `app/data/sources.py`; update the `SourceSpec` there.

## Schema

Every source is normalized to `app/data/schema.py::Example`:

- `text` — the **original** input, never normalized (normalization would erase
  attack signals like zero-width characters).
- `label` — `1` attack / `0` benign (the primary learning target).
- `category` — an `AttackCategory` only when the source provides one, else null.
- `source`, `group_id`, `split`.

## Leakage prevention (why the metrics will be honest)

Duplicate or near-duplicate prompts that land in both train and test are the
number-one cause of inflated accuracy. Two safeguards:

1. **Dedup** (`clean.py`): a normalized key (NFKC + casefold + whitespace
   collapse) identifies near-identical prompts; only one survives. The
   normalization is applied to the *key only* — training text stays original.
2. **Group-aware, stratified split** (`split.py`): whole groups go to a single
   split, and each split preserves the attack:benign ratio. Deterministic given
   a seed.

## Limitations

- Coverage skews toward direct, English/German, chat-style injection. Indirect
  (document/RAG) injection is under-represented; `prodnull/prompt-injection-repo-dataset`
  is a specialized option to add later.
- Dedup is exact-on-normalized-text; semantic near-duplicates (paraphrases) can
  still slip through. MinHash or embedding-based dedup is a future upgrade.
- Adversarially *evaded* samples (e.g. `Mindgard/...`) are best held out as a
  hard test set in Phase 3 rather than mixed into training.
