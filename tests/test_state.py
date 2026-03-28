"""Tests for state initialisation and data contracts."""
import asyncio
import time

import pytest

from flowstate.state import (
    Frame,
    ScreenCtx,
    SentimentScore,
    SentinelState,
    SharedSentinelState,
    SSEEvent,
    TaskContext,
    init_state,
)


def test_init_state_creates_all_primitives():
    async def _run():
        s = init_state()
        assert isinstance(s.webcam_fill_event, asyncio.Event)
        assert isinstance(s.handoff_trigger, asyncio.Event)
        assert isinstance(s.handoff_approved, asyncio.Event)
        assert isinstance(s.context_ready, asyncio.Event)
        assert isinstance(s.stop_control, asyncio.Event)
        assert isinstance(s.score_queue, asyncio.Queue)
        assert isinstance(s.sse_queue, asyncio.Queue)
        assert isinstance(s.webcam_lock, asyncio.Lock)
        assert isinstance(s.screen_lock, asyncio.Lock)
        return s

    s = asyncio.run(_run())
    assert s.current_state == SentinelState.CALM
    assert s.consecutive_stressed == 0


def test_webcam_buffer_maxlen():
    async def _run():
        s = init_state()
        for i in range(10):
            s.webcam_buffer.append(Frame(image_bytes=b"x", captured_at=float(i)))
        return len(s.webcam_buffer)

    assert asyncio.run(_run()) == 5  # maxlen=5


def test_sentiment_score_fields():
    score = SentimentScore(
        stress=0.7,
        fatigue=0.6,
        raw_label="stressed",
        frame_count=5,
        scored_at=time.monotonic(),
    )
    assert 0 <= score.stress <= 1
    assert 0 <= score.fatigue <= 1
    assert score.raw_label == "stressed"


def test_sse_event_contract():
    event = SSEEvent(
        type="status_update",
        data={"state": "calm", "consecutive": 0, "stress": 0.2, "fatigue": 0.15},
    )
    assert event.type == "status_update"
    assert "state" in event.data


def test_task_context_fields():
    ctx = TaskContext(
        task_type="coding",
        current_url=None,
        visible_text_summary="Working on FastAPI server",
        suggested_next_steps=["Fix auth", "Add tests"],
        codebase_context="",
        assessed_at=time.monotonic(),
    )
    assert ctx.task_type == "coding"
    assert len(ctx.suggested_next_steps) == 2


def test_sentinel_state_enum():
    assert SentinelState.CALM.value == "calm"
    assert SentinelState.CRITICAL.value == "critical"
    states = [s.value for s in SentinelState]
    assert set(states) == {"calm", "elevated", "stressed", "critical"}
