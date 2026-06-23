from app.decision.engine import Verdict, decide


def test_high_score_blocks() -> None:
    assert decide(0.9) is Verdict.BLOCK


def test_mid_score_flags() -> None:
    assert decide(0.5) is Verdict.FLAG


def test_low_score_allows() -> None:
    assert decide(0.1) is Verdict.ALLOW


def test_zero_allows() -> None:
    assert decide(0.0) is Verdict.ALLOW
