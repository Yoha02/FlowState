"""Orchestrator — drains score_queue and drives the state machine."""

import asyncio
import logging

from flowstate.state import SharedSentinelState, SentinelState, SSEEvent, SentimentScore
from flowstate.config import (
    STRESS_SCORE_CUTOFF,
    FATIGUE_SCORE_CUTOFF,
    RECOVERY_THRESHOLD,
    STRESS_THRESHOLD,
)
from flowstate.agents import negotiator, assessor, control

log = logging.getLogger(__name__)


def _map_state(stress: float) -> SentinelState:
    if stress >= STRESS_SCORE_CUTOFF:
        return SentinelState.STRESSED
    if stress >= RECOVERY_THRESHOLD:
        return SentinelState.ELEVATED
    return SentinelState.CALM


async def run(state: SharedSentinelState) -> None:
    while True:
        score: SentimentScore = await state.score_queue.get()
        state.sentiment_history.append(score)

        stress = score.stress
        fatigue = score.fatigue

        # Threshold logic
        if stress >= STRESS_SCORE_CUTOFF and fatigue >= FATIGUE_SCORE_CUTOFF:
            state.consecutive_stressed += 1
        elif stress < RECOVERY_THRESHOLD:
            state.consecutive_stressed = 0

        # Check critical threshold — only fire once per breach
        if (
            state.consecutive_stressed >= STRESS_THRESHOLD
            and not state.handoff_trigger.is_set()
        ):
            state.handoff_trigger.set()
            state.current_state = SentinelState.CRITICAL
            log.info("CRITICAL — handoff triggered (consecutive=%d)", state.consecutive_stressed)

            # Launch handoff pipeline as a background task
            asyncio.create_task(_run_handoff_pipeline(state))
        elif state.consecutive_stressed >= STRESS_THRESHOLD:
            state.current_state = SentinelState.CRITICAL
        else:
            state.current_state = _map_state(stress)

        # Push status update
        await state.sse_queue.put(SSEEvent(
            type="status_update",
            data={
                "state": state.current_state.value,
                "consecutive": state.consecutive_stressed,
                "stress": round(stress, 3),
                "fatigue": round(fatigue, 3),
            },
        ))


async def _run_handoff_pipeline(state: SharedSentinelState) -> None:
    """Chain: negotiator (consent) -> assessor (context) -> control (takeover)."""
    rejected = False
    try:
        await negotiator.run(state)
        await assessor.run(state)
        await control.run(state)
    except RuntimeError:
        # Negotiator timeout/rejection — keep scanning
        rejected = True
        log.info("Handoff rejected/timed out — will re-trigger on next stress")
    except Exception:
        log.exception("Handoff pipeline failed")
    finally:
        state.stop_control.clear()
        state.context_ready.clear()
        state.handoff_approved.clear()
        state.handoff_trigger.clear()
        if rejected:
            # Keep consecutive high so next stressed frame re-triggers
            state.consecutive_stressed = STRESS_THRESHOLD - 1
            state.current_state = SentinelState.STRESSED
            log.info("Handoff pipeline reset — ready to re-trigger")
        else:
            state.consecutive_stressed = 0
            state.current_state = SentinelState.CALM
            log.info("Handoff pipeline complete — reset to CALM")
