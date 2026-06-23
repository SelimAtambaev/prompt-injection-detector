"""Recorder: the seam between the proxy and persistence.

The proxy depends on a ``Recorder`` (injected), so tests substitute a
``NullRecorder`` and never write to a database. ``DBRecorder`` writes are
wrapped so a database hiccup is logged but never breaks the request path --
persistence is observability, not a reason to drop a user's request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import structlog

from app.core.config import settings

log = structlog.get_logger()


@dataclass
class InspectionData:
    request_id: str
    verdict: str
    risk_score: float
    top_category: str | None
    num_signals: int
    latency_ms: float
    prompt_preview: str


class Recorder(Protocol):
    def record(self, data: InspectionData) -> None: ...


class NullRecorder:
    def record(self, data: InspectionData) -> None:
        return None


class DBRecorder:
    def record(self, data: InspectionData) -> None:
        try:
            from app.storage.db import default_session_factory
            from app.storage.repository import add_inspection

            factory = default_session_factory()
            with factory() as session:
                add_inspection(session, **data.__dict__)
                session.commit()
        except Exception as exc:  # noqa: BLE001 -- persistence must never break a request
            log.warning("persistence_failed", error=str(exc))


def get_recorder() -> Recorder:
    return DBRecorder() if settings.persist_enabled else NullRecorder()
