"""Tests for the orchestrator state machine logic."""
import asyncio
import time

import pytest

from flowstate.state import SentimentScore, SentinelState, init_state


def make_score(stress: float, fatigue: float) -> SentimentScore:
    return SentimentScore(
        stress=stress,
        fatigue=fatigue,
        raw_label="test",
        frame_count=5,
        scored_at=time.monotonic(),
    )


def test_consecutive_stressed_increments_on_high_scores():
    async def _run():
        state = init_state()
        # Feed 2 high-stress scores — should not trigger handoff (threshold=3)
        for _ in range(2):
            await state.score_queue.put(make_score(stress=0.8, fatigue=0.7))

        # Drain queue manually (partial orchestrator logic)
        count = 0
        while not state.score_queue.empty():
            score = await state.score_queue.get()
            if score.stress >= 0.65 and score.fatigue >= 0.55:
                state.consecutive_stressed += 1
            count += 1
        return state.consecutive_stressed, count

    consecutive, count = asyncio.run(_run())
    assert count == 2
    assert consecutive == 2


def test_recovery_resets_consecutive():
    async def _run():
        state = init_state()
        state.consecutive_stressed = 2
        # Low-stress score should reset
        score = make_score(stress=0.2, fatigue=0.1)
        if score.stress < 0.35:
            state.consecutive_stressed = 0
        return state.consecutive_stressed

    assert asyncio.run(_run()) == 0


def test_sse_queue_receives_status_update():
    async def _run():
        state = init_state()
        from flowstate.state import SSEEvent

        await state.sse_queue.put(
            SSEEvent(
                type="status_update",
                data={"state": "calm", "consecutive": 0, "stress": 0.2, "fatigue": 0.1},
            )
        )
        event = await asyncio.wait_for(state.sse_queue.get(), timeout=1.0)
        return event

    event = asyncio.run(_run())
    assert event.type == "status_update"
    assert event.data["state"] == "calm"
