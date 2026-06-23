"""Database model for a persisted inspection.

One row per inspected request: the verdict, the risk score, and enough
context for the dashboard to show history and trends without re-reading logs.
We store a prompt *preview* (truncated/hashed per logging config), never raw
user input by default -- the same privacy stance as the logging layer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    verdict: Mapped[str] = mapped_column(String(16), index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    top_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    num_signals: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    prompt_preview: Mapped[str] = mapped_column(String(512), default="")
