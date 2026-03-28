"""Webcam capture loop — appends Frame objects to shared state."""

import asyncio
import logging
import time

import cv2
import numpy as np

from flowstate.state import SharedSentinelState, Frame
from flowstate.config import TICK_WEBCAM_SECONDS, WEBCAM_BUFFER_SIZE

log = logging.getLogger(__name__)


def _make_mock_frame() -> bytes:
    """Generate a 100x100 grey JPEG for when no camera is available."""
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


async def run(state: SharedSentinelState) -> None:
    cap = cv2.VideoCapture(0)
    use_mock = not cap.isOpened()
    if use_mock:
        log.warning("Webcam not available — using mock grey frames")
        cap.release()

    try:
        while True:
            if use_mock:
                jpeg_bytes = _make_mock_frame()
            else:
                ret, frame = cap.read()
                if not ret:
                    log.warning("Webcam read failed — falling back to mock")
                    use_mock = True
                    cap.release()
                    jpeg_bytes = _make_mock_frame()
                else:
                    _, buf = cv2.imencode(".jpg", frame)
                    jpeg_bytes = buf.tobytes()

            async with state.webcam_lock:
                state.webcam_buffer.append(
                    Frame(image_bytes=jpeg_bytes, captured_at=time.monotonic())
                )
                if len(state.webcam_buffer) >= WEBCAM_BUFFER_SIZE:
                    state.webcam_fill_event.set()

            await asyncio.sleep(TICK_WEBCAM_SECONDS)
    finally:
        if not use_mock:
            cap.release()
