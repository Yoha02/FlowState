"""Sentiment analysis agent loop — reads webcam frames, scores stress/fatigue."""
from __future__ import annotations

import logging
import time

from flowstate.state import SharedSentinelState, SentimentScore
from flowstate.tools.gemini import analyse_sentiment
from flowstate.tools.unkey import check_rate_limit

logger = logging.getLogger(__name__)


async def run(state: SharedSentinelState) -> None:
    """
    Loop forever:
      1. Wait for webcam_fill_event
      2. Check rate limit
      3. Analyse sentiment (or use neutral fallback if rate limited)
      4. Push score to queue and history
    """
    while True:
        try:
            await state.webcam_fill_event.wait()
            state.webcam_fill_event.clear()

            if state.demo_active:
                continue  # Skip real scoring during demo

            async with state.webcam_lock:
                frames = list(state.webcam_buffer)

            allowed = await check_rate_limit("flowstate-sentiment")
            if not allowed:
                logger.info("Rate limited — using neutral score")
                score = SentimentScore(
                    stress=0.2,
                    fatigue=0.2,
                    raw_label="calm",
                    frame_count=len(frames),
                    scored_at=time.monotonic(),
                )
            else:
                score = await analyse_sentiment([f.image_bytes for f in frames])

            await state.score_queue.put(score)
            state.sentiment_history.append(score)
            logger.debug("Scored: stress=%.2f fatigue=%.2f label=%s",
                         score.stress, score.fatigue, score.raw_label)
        except Exception:
            logger.exception("Sentiment agent error — continuing")
