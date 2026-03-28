"""FastAPI server — SSE bridge and handoff response endpoint."""

import asyncio
import json
import logging
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from flowstate.state import SharedSentinelState

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


def set_state(s: SharedSentinelState) -> None:
    global _state
    _state = s


class HandoffResponse(BaseModel):
    approved: bool


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status/stream")
async def status_stream():
    async def event_generator():
        heartbeat_interval = 5.0
        while True:
            try:
                event = await asyncio.wait_for(_state.sse_queue.get(), timeout=heartbeat_interval)
                yield {
                    "event": event.type,
                    "data": json.dumps(event.data),
                }
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": ""}

    return EventSourceResponse(event_generator())


@app.post("/handoff/respond")
async def handoff_respond(body: HandoffResponse):
    if body.approved:
        _state.handoff_approved.set()
    else:
        _state.handoff_trigger.clear()
        _state.consecutive_stressed = 0
    return {"ok": True}
