"""Tests for Gemini tool wrappers — mock mode (no API key required)."""
import asyncio
import os

import pytest


def test_mock_sentiment_when_no_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    # Force reload config
    import importlib
    import flowstate.config as cfg
    importlib.reload(cfg)
    import flowstate.tools.gemini as gemini_mod
    importlib.reload(gemini_mod)

    async def _run():
        return await gemini_mod.analyse_sentiment([])

    score = asyncio.run(_run())
    assert score.stress == 0.2
    assert score.fatigue == 0.2
    assert score.raw_label == "calm"


def test_mock_task_context_when_no_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    import importlib
    import flowstate.config as cfg
    importlib.reload(cfg)
    import flowstate.tools.gemini as gemini_mod
    importlib.reload(gemini_mod)

    async def _run():
        return await gemini_mod.analyse_screen([], "Test Window")

    ctx = asyncio.run(_run())
    assert ctx.task_type == "unknown"
    assert "Mock" in ctx.visible_text_summary


def test_mock_sentiment_returns_frame_count(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    import importlib
    import flowstate.config as cfg
    importlib.reload(cfg)
    import flowstate.tools.gemini as gemini_mod
    importlib.reload(gemini_mod)

    async def _run():
        return await gemini_mod.analyse_sentiment([b"fake_frame"] * 3)

    score = asyncio.run(_run())
    assert score.frame_count == 3
