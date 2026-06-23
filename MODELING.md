# Modeling (Phase 3)

The Layer-2 ML detector: embed text, classify attack vs. benign, evaluate
honestly. Code in `app/detection/ml/`.

## Architecture

```
text -> Embedder -> vector -> LogisticRegression -> P(attack) -> Signal
```

Run on your machine after building the dataset (Phase 2):

```bash
pip install -e ".[ml]"                              # adds scikit-learn + sentence-transformers (torch)
python -m app.detection.ml.train                    # writes models/ml_classifier.joblib
python -m app.detection.ml.evaluate                 # prints the metrics report
```

## Choices and trade-offs

**Embedder: sentence-transformers (`all-MiniLM-L6-v2`) by default.** Small, fast,
CPU-friendly, and semantically meaningful (generalizes to unseen phrasings). A
dependency-light `HashingEmbedder` (scikit-learn only, no torch) is provided as
a fallback for CI and quick experiments; it's bag-of-ngrams, so weaker on novel
wording. Bigger embedding models trade latency for a little accuracy — measure
before reaching for them, since this sits on the request hot path.

**Classifier: Logistic Regression.** Fast, gives *calibrated probabilities* (the
Phase-4 risk engine needs a real probability, not just a label), and is
interpretable. `class_weight="balanced"` prevents the minority class from being
ignored. Gradient boosting or an SVM would add capacity at the cost of speed and
calibration; a fine-tuned DeBERTa transformer is the heavy Layer-3 option for
later.

**Binary, not 8-way.** As established in DATA.md, the data supports a binary
target. The ML signal is therefore *category-agnostic* — it reports an attack
likelihood, and the heuristic layer supplies the category. This is reflected in
`Signal.category` being `None` for ML signals.

## Evaluation philosophy

`evaluate.py` reports precision, recall, F1, ROC-AUC, the confusion matrix, the
**false-positive rate** (over-blocking legitimate users is the real cost), and
**per-example latency** (hot path). A single accuracy number is not a result;
the trade-off and the chosen operating threshold are. Tune the threshold against
your tolerance for false positives rather than leaving it at 0.5 blindly.

## Honest limitations

- The model is only as good as the corpus — see DATA.md's coverage gaps.
- Adversarially *evaded* inputs (character injection, paraphrase) are designed to
  beat exactly this kind of classifier; hold out a hard set (e.g. the Mindgard
  evasion samples) and expect lower numbers there. Reporting that gap is more
  credible than hiding it.
- Embedding + classify adds latency the heuristic layer doesn't have, which is
  why it's Layer 2 (run after the cheap heuristics), not Layer 1.
