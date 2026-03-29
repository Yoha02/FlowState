"""Gemini Flash vision wrapper for sentiment and screen analysis."""
from __future__ import annotations

import base64
import json
import logging
import time

from google import genai

from flowstate.config import GEMINI_API_KEY
from flowstate.state import SentimentScore, TaskContext

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _mock_sentiment(frame_count: int) -> SentimentScore:
    return SentimentScore(
        stress=0.2,
        fatigue=0.2,
        raw_label="calm",
        frame_count=frame_count,
        scored_at=time.monotonic(),
    )


def _mock_task_context() -> TaskContext:
    return TaskContext(
        task_type="unknown",
        current_url=None,
        visible_text_summary="Mock screen analysis — no Gemini key configured.",
        suggested_next_steps=["Configure GEMINI_API_KEY", "Retry analysis", "Check logs"],
        codebase_context="",
        assessed_at=time.monotonic(),
    )


async def analyse_sentiment(frames: list[bytes]) -> SentimentScore:
    """Send up to 5 JPEG frames to Gemini and return a SentimentScore."""
    if not GEMINI_API_KEY or not frames:
        return _mock_sentiment(len(frames) if frames else 0)

    try:
        parts = []
        for frame in frames[:5]:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(frame).decode(),
                }
            })
        parts.append(
            "Analyse the facial expressions in these webcam frames for signs of "
            "stress and fatigue. Return ONLY valid JSON with no markdown: "
            '{"stress": <float 0-1>, "fatigue": <float 0-1>, '
            '"label": "<calm|elevated|stressed|critical>"}'
        )

        client = _get_client()
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=parts
        )
        text = response.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        data = json.loads(text)
        return SentimentScore(
            stress=max(0.0, min(1.0, float(data.get("stress", 0.2)))),
            fatigue=max(0.0, min(1.0, float(data.get("fatigue", 0.2)))),
            raw_label=data.get("label", "calm"),
            frame_count=len(frames),
            scored_at=time.monotonic(),
        )
    except Exception:
        logger.exception("Gemini sentiment analysis failed")
        return _mock_sentiment(len(frames))


async def analyse_screen(screenshots: list[bytes], window_title: str) -> TaskContext:
    """Send up to 5 screen screenshots to Gemini and return a TaskContext."""
    if not GEMINI_API_KEY or not screenshots:
        return _mock_task_context()

    try:
        parts = []
        for shot in screenshots[:5]:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(shot).decode(),
                }
            })
        parts.append(
            f"Window title: {window_title}\n\n"
            "What is this developer working on? Identify the task type "
            "(coding, browsing, terminal, writing, or unknown), current URL if visible, "
            "and suggest 3 concrete next steps an AI agent could take to help. "
            "Return ONLY valid JSON with no markdown: "
            '{"task_type": "<type>", "url": "<url or null>", '
            '"summary": "<brief summary>", "next_steps": ["step1", "step2", "step3"]}'
        )

        client = _get_client()
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=parts
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        data = json.loads(text)
        return TaskContext(
            task_type=data.get("task_type", "unknown"),
            current_url=data.get("url"),
            visible_text_summary=data.get("summary", ""),
            suggested_next_steps=data.get("next_steps", []),
            codebase_context="",
            assessed_at=time.monotonic(),
        )
    except Exception:
        logger.exception("Gemini screen analysis failed")
        return _mock_task_context()
