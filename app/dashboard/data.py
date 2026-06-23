"""Dashboard data layer.

Pulls everything the dashboard renders into a plain dataclass, with NO Streamlit
or Plotly dependency, so it can be unit-tested without a UI. The Streamlit app
(app.py) is a thin renderer on top of this.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.storage.db import default_session_factory
from app.storage.repository import (
    category_counts,
    recent_inspections,
    summary,
    verdict_counts,
)


@dataclass
class DashboardData:
    summary: dict = field(default_factory=dict)
    verdicts: dict = field(default_factory=dict)
    categories: dict = field(default_factory=dict)
    recent: list[dict] = field(default_factory=list)


def load_dashboard_data(session: Session | None = None, recent_limit: int = 50) -> DashboardData:
    own_session = session is None
    if session is None:
        session = default_session_factory()()
    try:
        recent = [
            {
                "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
                "verdict": r.verdict,
                "risk_score": r.risk_score,
                "category": r.top_category or "—",
                "latency_ms": r.latency_ms,
                "preview": r.prompt_preview,
            }
            for r in recent_inspections(session, recent_limit)
        ]
        return DashboardData(
            summary=summary(session),
            verdicts=verdict_counts(session),
            categories=category_counts(session),
            recent=recent,
        )
    finally:
        if own_session:
            session.close()
