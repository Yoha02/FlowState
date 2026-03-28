"""Computer control agent — Claude Computer Use takes over GCP Cloud Shell."""

import asyncio
import logging

import anthropic

from flowstate.state import SharedSentinelState, SSEEvent, TaskContext
from flowstate.config import ANTHROPIC_API_KEY, DEMO_GCP_PROJECT, DEMO_CLOUD_RUN_SERVICE

log = logging.getLogger(__name__)


async def run(state: SharedSentinelState):
    """
    One-shot: read task_context, take over via Claude Computer Use.
    Pushes action SSE events so the frontend ActionFeed shows live steps.

    Falls back to a mock if ANTHROPIC_API_KEY is not set.
    """
    if not ANTHROPIC_API_KEY:
        log.info("Control: no API key — running mock pipeline")
        await _mock_control(state)
        return

    log.info("Control: starting real Computer Use pipeline")
    await _real_control(state)


async def _mock_control(state: SharedSentinelState):
    """Demo-safe mock that pushes realistic action steps."""
    steps = [
        ("Opening GCP Cloud Shell...", "browser"),
        ("Running: gcloud logging read --limit=20", "terminal"),
        ("Identified issue: Missing API_KEY env var in Cloud Run config", "search"),
        ("Running: gcloud run services update --set-env-vars API_KEY=***", "terminal"),
        ("Service healthy — 0 errors in last 60 seconds", "check"),
    ]
    for step, icon in steps:
        await asyncio.sleep(1.5)
        await state.sse_queue.put(SSEEvent(
            type="action",
            data={"step": step, "icon": icon},
        ))

    await asyncio.sleep(0.5)
    await state.sse_queue.put(SSEEvent(
        type="done",
        data={"message": "Task complete. Control returned to you."},
    ))
    state.stop_control.set()


async def _real_control(state: SharedSentinelState):
    """Real Claude Computer Use implementation."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    ctx: TaskContext = state.task_context

    system = (
        f"You are taking over from a stressed developer.\n"
        f"Task: {ctx.visible_text_summary}\n"
        f"Codebase context: {ctx.codebase_context}\n\n"
        f"Open a browser. Navigate to https://shell.cloud.google.com\n"
        f"Diagnose and fix the Cloud Run service issue.\n"
        f"Be concise and efficient — the developer is resting."
    )

    messages = [{"role": "user", "content": system}]

    # Computer use tool loop
    max_iterations = 20
    for i in range(max_iterations):
        if state.stop_control.is_set():
            log.info("Control: stop_control set — exiting loop at iteration %d", i)
            break

        response = client.beta.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1024,
            tools=[
                {
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": 1920,
                    "display_height_px": 1080,
                },
            ],
            messages=messages,
            betas=["computer-use-2025-01-24"],
        )

        if response.stop_reason == "end_turn":
            log.info("Control: model ended turn — finishing")
            break

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            break

        tool_results = []
        for tu in tool_uses:
            action = tu.input.get("action", "")
            await state.sse_queue.put(SSEEvent(
                type="action",
                data={"step": f"{action}: {str(tu.input)[:80]}", "icon": "terminal"},
            ))
            # In real use, execute the computer action here via a local agent
            # For now, return a placeholder result
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": "Action executed.",
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    await state.sse_queue.put(SSEEvent(
        type="done",
        data={"message": "Task complete. Control returned to you."},
    ))
    state.stop_control.set()
