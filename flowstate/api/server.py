"""FastAPI server — SSE bridge, handoff response, and demo trigger."""

import asyncio
import json
import logging
import time
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from flowstate.state import SharedSentinelState, SentimentScore

log = logging.getLogger(__name__)

app = FastAPI(title="FlowState API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_state: SharedSentinelState | None = None
_subscribers: list[asyncio.Queue] = []


def set_state(s: SharedSentinelState) -> None:
    global _state
    _state = s


async def _broadcast_loop():
    """Drain the single sse_queue and fan out to all subscriber queues."""
    while True:
        event = await _state.sse_queue.get()
        dead = []
        for i, q in enumerate(_subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(i)
        # Remove dead/full subscribers in reverse order
        for i in reversed(dead):
            _subscribers.pop(i)


class HandoffResponse(BaseModel):
    approved: bool


@app.on_event("startup")
async def startup():
    asyncio.create_task(_broadcast_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status/stream")
async def status_stream():
    sub_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(sub_queue)

    async def event_generator():
        try:
            heartbeat_interval = 5.0
            while True:
                try:
                    event = await asyncio.wait_for(sub_queue.get(), timeout=heartbeat_interval)
                    yield {
                        "event": event.type,
                        "data": json.dumps(event.data),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "heartbeat", "data": ""}
        finally:
            if sub_queue in _subscribers:
                _subscribers.remove(sub_queue)

    return EventSourceResponse(event_generator())


@app.post("/handoff/respond")
async def handoff_respond(body: HandoffResponse):
    if body.approved:
        _state.handoff_approved.set()
    else:
        _state.handoff_trigger.clear()
        _state.consecutive_stressed = 0
    return {"ok": True}


@app.post("/plan/confirm")
async def plan_confirm():
    """User confirmed the agent's proposed plan — proceed with execution."""
    _state.plan_confirmed.set()
    return {"ok": True}


@app.post("/demo/start")
async def demo_start():
    """Inject escalating stress scores into the real pipeline.

    Sequence (runs in background):
      t=0s   stress=0.30  → CALM
      t=3s   stress=0.50  → ELEVATED
      t=6s   stress=0.70  → STRESSED (consecutive=1)
      t=9s   stress=0.80  → STRESSED (consecutive=2)
      t=12s  stress=0.90  → STRESSED (consecutive=3) → CRITICAL → handoff fires
    Then the real orchestrator→negotiator→assessor→control pipeline runs.
    """
    asyncio.create_task(_demo_escalation())
    return {"ok": True, "message": "Demo escalation started — watch the UI"}


async def _demo_escalation():
    """Push fake SentimentScores into score_queue so the real orchestrator triggers."""
    # Pause real sentiment loop and reset state
    _state.demo_active = True
    _state.consecutive_stressed = 0
    _state.handoff_trigger.clear()
    _state.handoff_approved.clear()
    _state.stop_control.clear()

    ramp = [
        (0.30, 0.20, "calm"),
        (0.50, 0.40, "elevated"),
        (0.70, 0.60, "stressed"),
        (0.80, 0.70, "stressed"),
        (0.90, 0.80, "critical"),
    ]

    try:
        for stress, fatigue, label in ramp:
            score = SentimentScore(
                stress=stress,
                fatigue=fatigue,
                raw_label=label,
                frame_count=5,
                scored_at=time.monotonic(),
            )
            await _state.score_queue.put(score)
            log.info("Demo: injected stress=%.2f fatigue=%.2f label=%s", stress, fatigue, label)
            await asyncio.sleep(3.0)
    finally:
        # Re-enable real sentiment after pipeline completes
        _state.demo_active = False
