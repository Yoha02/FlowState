"""Screen capture loop — appends ScreenCtx objects to shared state."""

import asyncio
import logging
import time

import mss
import mss.tools

from flowstate.state import SharedSentinelState, ScreenCtx
from flowstate.config import TICK_SCREEN_SECONDS

log = logging.getLogger(__name__)


def _get_active_window_title() -> str:
    """Return the active window title (Windows only, empty string fallback)."""
    try:
        import win32gui  # type: ignore[import-untyped]
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def _extract_browser_url(title: str) -> str | None:
    """Heuristically extract a URL hint from a browser window title."""
    browser_suffixes = [
        " - Google Chrome",
        " - Mozilla Firefox",
        " - Microsoft Edge",
        " - Brave",
        " - Opera",
    ]
    for suffix in browser_suffixes:
        if title.endswith(suffix):
            return title[: -len(suffix)]
    return None


def _make_mock_screenshot() -> bytes:
    """Generate a tiny grey PNG for headless environments."""
    import struct, zlib
    # Minimal 1x1 grey PNG
    raw = b'\x00\x80\x80\x80'
    compressed = zlib.compress(raw)
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', compressed)
            + chunk(b'IEND', b''))


async def run(state: SharedSentinelState) -> None:
    use_mock = False
    sct = None
    monitor = None

    try:
        sct = mss.mss()
        monitor = sct.monitors[1]
    except Exception:
        log.warning("Screen capture not available (headless?) — using mock screenshots")
        use_mock = True

    try:
        while True:
            if use_mock:
                png_bytes = _make_mock_screenshot()
                title = "Mock — no display"
            else:
                screenshot = sct.grab(monitor)
                png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
                title = _get_active_window_title()

            url = _extract_browser_url(title)

            async with state.screen_lock:
                state.screen_buffer.append(
                    ScreenCtx(
                        image_bytes=png_bytes,
                        window_title=title,
                        url=url,
                        captured_at=time.monotonic(),
                    )
                )

            await asyncio.sleep(TICK_SCREEN_SECONDS)
    finally:
        if sct:
            sct.close()
