"""Repository: all database reads/writes the app and dashboard need.

Keeping queries here (not scattered in the proxy or dashboard) means there's
one place to optimize or port when the backend changes from SQLite to Postgres.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.storage.models import Inspection


def add_inspection(
    session: Session,
    *,
    request_id: str,
    verdict: str,
    risk_score: float,
    top_category: str | None,
    num_signals: int,
    latency_ms: float,
    prompt_preview: str,
) -> Inspection:
    row = Inspection(
        request_id=request_id,
        verdict=verdict,
        risk_score=risk_score,
        top_category=top_category,
        num_signals=num_signals,
        latency_ms=latency_ms,
        prompt_preview=prompt_preview,
    )
    session.add(row)
    return row


def recent_inspections(session: Session, limit: int = 50) -> list[Inspection]:
    stmt = select(Inspection).order_by(Inspection.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars().all())


def verdict_counts(session: Session) -> dict[str, int]:
    stmt = select(Inspection.verdict, func.count()).group_by(Inspection.verdict)
    return {verdict: count for verdict, count in session.execute(stmt).all()}


def category_counts(session: Session) -> dict[str, int]:
    stmt = (
        select(Inspection.top_category, func.count())
        .where(Inspection.top_category.is_not(None))
        .group_by(Inspection.top_category)
    )
    return {category: count for category, count in session.execute(stmt).all()}


def summary(session: Session) -> dict[str, float | int]:
    counts = verdict_counts(session)
    total = sum(counts.values())
    blocked = counts.get("block", 0)
    avg_latency = session.execute(select(func.avg(Inspection.latency_ms))).scalar() or 0.0
    return {
        "total": total,
        "blocked": blocked,
        "flagged": counts.get("flag", 0),
        "allowed": counts.get("allow", 0),
        "block_rate": round(blocked / total, 4) if total else 0.0,
        "avg_latency_ms": round(float(avg_latency), 3),
    }
