"""Tests for the dashboard data layer (no Streamlit needed)."""

import pytest

from app.dashboard.data import load_dashboard_data
from app.storage.db import make_session_factory
from app.storage.repository import add_inspection


@pytest.fixture
def session(tmp_path):
    factory = make_session_factory(f"sqlite:///{tmp_path / 'dash.db'}")
    with factory() as s:
        yield s


def _add(session, verdict, score, cat):
    add_inspection(
        session,
        request_id="r",
        verdict=verdict,
        risk_score=score,
        top_category=cat,
        num_signals=1,
        latency_ms=2.0,
        prompt_preview="p",
    )


def test_empty_database(session):
    data = load_dashboard_data(session)
    assert data.summary["total"] == 0
    assert data.recent == []


def test_populated_database(session):
    _add(session, "allow", 0.1, None)
    _add(session, "block", 0.9, "jailbreak")
    _add(session, "block", 0.8, "data_exfiltration")
    session.commit()

    data = load_dashboard_data(session)
    assert data.summary["total"] == 3
    assert data.verdicts["block"] == 2
    assert "jailbreak" in data.categories
    assert len(data.recent) == 3
    assert {"time", "verdict", "risk_score", "category", "latency_ms", "preview"} <= set(
        data.recent[0].keys()
    )
