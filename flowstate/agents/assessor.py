"""Task assessor — runs once per handoff trigger to build TaskContext."""
from __future__ import annotations

import logging

from flowstate.state import SharedSentinelState
from flowstate.tools.gemini import analyse_screen
from flowstate.tools.augment import get_codebase_context

logger = logging.getLogger(__name__)


async def run(state: SharedSentinelState) -> None:
    """
    One-shot function called when handoff is approved.

    1. Snapshot screen_buffer (last 5 frames)
    2. Call analyse_screen → TaskContext
    3. If coding task, enrich with Augment codebase context
    4. Write result to state and signal context_ready
    """
    try:
        async with state.screen_lock:
            snapshots = list(state.screen_buffer)[-5:]

        screenshots = [s.image_bytes for s in snapshots]
        window_titles = [s.window_title for s in snapshots]
        title = window_titles[-1] if window_titles else ""

        ctx = await analyse_screen(screenshots, title)

        if ctx.task_type == "coding":
            ctx.codebase_context = await get_codebase_context(ctx.visible_text_summary)

        state.task_context = ctx
        state.context_ready.set()
        logger.info("Task context ready: type=%s", ctx.task_type)
    except Exception:
        logger.exception("Assessor failed — signalling context_ready with None")
        state.context_ready.set()
