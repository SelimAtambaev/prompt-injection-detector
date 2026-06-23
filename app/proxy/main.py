r"""FastAPI reverse proxy.

Request flow (Phase 4 -- both detection layers now wired in):
    client -> /v1/chat -> DetectionEngine (heuristics + ML) -> risk scoring
                       -> decision (allow/flag/block) -> [block | forward to LLM]
                       -> structured log (always)

Remaining limitations (documented; addressed later):
  * Inspects only the latest user message (multi-turn handling is future work).
  * No output-side inspection.
"""

from __future__ import annotations

import hashlib
import time
import uuid

import structlog
from fastapi import BackgroundTasks, Depends, FastAPI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.decision.engine import Verdict, decide
from app.detection.engine import build_default_engine
from app.logging.setup import configure_logging
from app.proxy.llm import LLMClient, get_llm_client
from app.scoring.engine import score_result
from app.storage.recorder import InspectionData, Recorder, get_recorder

configure_logging()
log = structlog.get_logger()

app = FastAPI(title="Prompt Injection Firewall", version="0.4.0")
engine = build_default_engine()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    model: str | None = None


class ChatResponse(BaseModel):
    request_id: str
    verdict: str
    risk_score: float
    blocked: bool
    response: str | None = None
    reasons: list[str] = Field(default_factory=list)


def _latest_user_text(messages: list[Message]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return ""


def _preview(text: str) -> str:
    mode = settings.prompt_log_mode
    if mode == "full":
        return text
    if mode == "hashed":
        return "sha256:" + hashlib.sha256(text.encode()).hexdigest()[:16]
    return text[: settings.prompt_log_max_chars]


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "layers": engine.layer_names}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm_client),
    recorder: Recorder = Depends(get_recorder),
) -> ChatResponse:
    request_id = str(uuid.uuid4())
    user_text = _latest_user_text(req.messages)

    result = await engine.detect(user_text)
    risk = score_result(result)
    verdict = decide(risk.score)

    log.info(
        "request_inspected",
        request_id=request_id,
        verdict=verdict.value,
        risk_score=risk.score,
        contributions=risk.contributions,
        detect_latency_ms=round(result.latency_ms, 3),
        prompt_preview=_preview(user_text),
    )

    top = risk.top_signal
    top_category = top.category.value if (top and top.category) else None
    background.add_task(
        recorder.record,
        InspectionData(
            request_id=request_id,
            verdict=verdict.value,
            risk_score=risk.score,
            top_category=top_category,
            num_signals=len(result.signals),
            latency_ms=round(result.latency_ms, 3),
            prompt_preview=_preview(user_text),
        ),
    )

    if verdict is Verdict.BLOCK:
        return ChatResponse(
            request_id=request_id,
            verdict=verdict.value,
            risk_score=risk.score,
            blocked=True,
            reasons=[s.evidence for s in result.signals],
        )

    answer = await llm.complete(
        messages=[m.model_dump() for m in req.messages],
        model=req.model or settings.openai_model,
    )
    return ChatResponse(
        request_id=request_id,
        verdict=verdict.value,
        risk_score=risk.score,
        blocked=False,
        response=answer,
    )
