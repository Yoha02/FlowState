"""Shared state — the single source of truth passed between all agents.

All asyncio primitives live here. Workers read from PLAN.md for context,
but this file defines the data contracts every agent must honour.
"""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SentinelState(str, Enum):
    CALM = "calm"
    ELEVATED = "elevated"
    STRESSED = "stressed"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Data objects (passed between agents)
# ---------------------------------------------------------------------------

@dataclass
class Frame:
    """A single captured webcam frame."""
    image_bytes: bytes
    captured_at: float  # time.monotonic()


@dataclass
class ScreenCtx:
    """A single screen capture with metadata."""
    image_bytes: bytes
    window_title: str
    url: Optional[str]   # browser URL if active, else None
    captured_at: float


@dataclass
class SentimentScore:
    """Output of SentimentAnalyzer for one batch of frames."""
    stress: float           # 0.0 (calm) → 1.0 (critical)
    fatigue: float          # 0.0 (alert) → 1.0 (exhausted)
    raw_label: str          # "calm" | "elevated" | "stressed" | "critical"
    frame_count: int        # number of frames analysed
    scored_at: float        # time.monotonic()


@dataclass
class TaskContext:
    """Output of TaskAssessor — what was the user working on."""
    task_type: str                  # "coding" | "browsing" | "terminal" | "writing" | "unknown"
    current_url: Optional[str]
    visible_text_summary: str       # brief Gemini summary of screen content
    suggested_next_steps: list[str] # what the agent should do
    codebase_context: str           # Augment Code findings, empty string if N/A
    assessed_at: float


# ---------------------------------------------------------------------------
# SSE event shapes (used by api/sse.py → frontend)
# ---------------------------------------------------------------------------

@dataclass
class SSEEvent:
    """Sent to frontend via SSE stream."""
    type: str   # "status_update" | "handoff_trigger" | "action" | "task_context" | "done"
    data: dict  # payload varies by type


# ---------------------------------------------------------------------------
# Shared sentinel state
# ---------------------------------------------------------------------------

@dataclass
class SharedSentinelState:
    """
    Single instance created in main.py and passed by reference to every agent.

    Locks:
      webcam_lock  — protects webcam_buffer reads/writes
      screen_lock  — protects screen_buffer reads/writes

    Events:
      webcam_fill_event   — set when buffer reaches WEBCAM_BUFFER_SIZE
      handoff_trigger     — set by orchestrator when threshold crossed
      handoff_approved    — set by negotiator when user clicks Take Over
      context_ready       — set by assessor when TaskContext is written
      stop_control        — set by UI kill-switch or on completion

    Queues:
      score_queue         — SentimentScore objects from sentiment agent
      sse_queue           — SSEEvent objects for frontend SSE stream
    """

    # Capture buffers
    webcam_buffer: deque = field(default_factory=lambda: deque(maxlen=5))
    screen_buffer: deque = field(default_factory=lambda: deque(maxlen=10))

    # Sentiment history (last 20 scores)
    sentiment_history: deque = field(default_factory=lambda: deque(maxlen=20))

    # State machine
    current_state: SentinelState = SentinelState.CALM
    consecutive_stressed: int = 0

    # Task context (written by assessor, read by control)
    task_context: Optional[TaskContext] = None

    # Rate limit tracking (from Unkey responses)
    rate_limit_remaining: int = 100

    # --- asyncio primitives (initialised in main.py via init_events()) ---
    webcam_fill_event: Optional[asyncio.Event] = field(default=None, repr=False)
    handoff_trigger: Optional[asyncio.Event] = field(default=None, repr=False)
    handoff_approved: Optional[asyncio.Event] = field(default=None, repr=False)
    context_ready: Optional[asyncio.Event] = field(default=None, repr=False)
    stop_control: Optional[asyncio.Event] = field(default=None, repr=False)

    score_queue: Optional[asyncio.Queue] = field(default=None, repr=False)
    sse_queue: Optional[asyncio.Queue] = field(default=None, repr=False)

    webcam_lock: Optional[asyncio.Lock] = field(default=None, repr=False)
    screen_lock: Optional[asyncio.Lock] = field(default=None, repr=False)


def init_state() -> SharedSentinelState:
    """Create and initialise a SharedSentinelState with all asyncio primitives."""
    s = SharedSentinelState()
    s.webcam_fill_event = asyncio.Event()
    s.handoff_trigger = asyncio.Event()
    s.handoff_approved = asyncio.Event()
    s.context_ready = asyncio.Event()
    s.stop_control = asyncio.Event()
    s.score_queue = asyncio.Queue()
    s.sse_queue = asyncio.Queue(maxsize=100)
    s.webcam_lock = asyncio.Lock()
    s.screen_lock = asyncio.Lock()
    return s
