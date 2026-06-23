"""Storage tests against a throwaway SQLite database (no app DB touched)."""

import pytest

from app.storage.db import make_session_factory
from app.storage.repository import add_inspection, recent_inspections, summary, verdict_counts


@pytest.fixture
def session(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    factory = make_session_factory(url)
    with factory() as s:
        yield s


def _add(session, verdict, score, cat=None):
    add_inspection(
        session,
        request_id="r",
        verdict=verdict,
        risk_score=score,
        top_category=cat,
        num_signals=1,
        latency_ms=2.0,
        prompt_preview="preview",
    )
    session.commit()


def test_record_and_read_back(session):
    _add(session, "block", 0.95, "instruction_override")
    rows = recent_inspections(session)
    assert len(rows) == 1
    assert rows[0].verdict == "block"
    assert rows[0].top_category == "instruction_override"


def test_verdict_counts(session):
    _add(session, "allow", 0.1)
    _add(session, "allow", 0.2)
    _add(session, "block", 0.9)
    counts = verdict_counts(session)
    assert counts == {"allow": 2, "block": 1}


def test_summary_computes_block_rate(session):
    _add(session, "allow", 0.1)
    _add(session, "block", 0.9)
    _add(session, "flag", 0.5)
    s = summary(session)
    assert s["total"] == 3
    assert s["blocked"] == 1
    assert s["block_rate"] == round(1 / 3, 4)
    assert s["avg_latency_ms"] == 2.0


def test_recent_is_newest_first(session):
    _add(session, "allow", 0.1)
    _add(session, "block", 0.9)
    rows = recent_inspections(session, limit=10)
    assert len(rows) == 2  # ordered by created_at desc
