from app.detection.base import DetectionResult, Signal
from app.detection.taxonomy import DEFAULT_SEVERITY
from app.detection.taxonomy import AttackCategory as AC
from app.scoring.engine import score_result


def _sig(cat, conf, detector="t"):
    return Signal(category=cat, confidence=conf, detector=detector, evidence="x")


def test_empty_result_is_zero() -> None:
    assert score_result(DetectionResult()).score == 0.0


def test_single_signal_is_confidence_times_severity() -> None:
    r = DetectionResult(signals=[_sig(AC.INSTRUCTION_OVERRIDE, 0.85)])
    expected = 0.85 * DEFAULT_SEVERITY[AC.INSTRUCTION_OVERRIDE]  # 0.765
    assert abs(score_result(r).score - expected) < 1e-3


def test_corroborating_signals_compound_above_any_single() -> None:
    r = DetectionResult(
        signals=[_sig(AC.INSTRUCTION_OVERRIDE, 0.6), _sig(AC.DATA_EXFILTRATION, 0.6)]
    )
    singles = [
        0.6 * DEFAULT_SEVERITY[AC.INSTRUCTION_OVERRIDE],
        0.6 * DEFAULT_SEVERITY[AC.DATA_EXFILTRATION],
    ]
    assert score_result(r).score > max(singles)


def test_ml_signal_uses_ml_weight() -> None:
    r = DetectionResult(
        signals=[Signal(category=None, confidence=0.9, detector="ml_v1", evidence="p")]
    )
    assert abs(score_result(r, ml_weight=1.0).score - 0.9) < 1e-3


def test_low_severity_high_confidence_scores_below_high_severity() -> None:
    encoding = score_result(DetectionResult(signals=[_sig(AC.ENCODING, 0.9)])).score
    exfil = score_result(DetectionResult(signals=[_sig(AC.DATA_EXFILTRATION, 0.9)])).score
    assert encoding < exfil


def test_top_signal_is_highest_contributor() -> None:
    r = DetectionResult(signals=[_sig(AC.ENCODING, 0.5), _sig(AC.DATA_EXFILTRATION, 0.8)])
    assert score_result(r).top_signal.category is AC.DATA_EXFILTRATION
