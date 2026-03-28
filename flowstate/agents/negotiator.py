"""Handoff negotiator — fires the UI consent modal, waits for user response."""

import asyncio
import logging

from flowstate.state import SharedSentinelState, SSEEvent, SentinelState
from flowstate.config import HANDOFF_TIMEOUT_SECONDS

log = logging.getLogger(__name__)


async def run(state: SharedSentinelState):
    """
    Continuous loop: wait for handoff_trigger -> fire modal -> wait for approval/timeout -> reset.

    Returns when the user approves handoff so the orchestrator can chain assessor + control.
    """
    while True:
        await state.handoff_trigger.wait()

        # Build evidence from last 3 sentiment scores
        recent = list(state.sentiment_history)[-3:]
        avg_stress = sum(s.stress for s in recent) / max(len(recent), 1)
        evidence = f"Elevated stress ({avg_stress:.0%}) detected for {len(recent) * 5}+ seconds"

        log.info("Negotiator: firing handoff modal — %s", evidence)

        # Fire modal via SSE
        await state.sse_queue.put(SSEEvent(
            type="handoff_trigger",
            data={"evidence": evidence, "task_summary": "Analysing your screen..."},
        ))

        # Wait for user response
        try:
            await asyncio.wait_for(
                state.handoff_approved.wait(),
                timeout=HANDOFF_TIMEOUT_SECONDS,
            )
            log.info("Negotiator: handoff APPROVED by user")
            return  # Approved — caller chains assessor + control
        except asyncio.TimeoutError:
            log.info("Negotiator: handoff timed out / rejected — resetting to CALM")
            state.consecutive_stressed = 0
            state.current_state = SentinelState.CALM
            state.handoff_trigger.clear()
            state.handoff_approved.clear()
            await state.sse_queue.put(SSEEvent(
                type="status_update",
                data={
                    "state": "calm",
                    "consecutive": 0,
                    "stress": 0.2,
                    "fatigue": 0.2,
                },
            ))
