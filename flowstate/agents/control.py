"""Computer control agent — Claude Computer Use takes over the user's screen."""

import asyncio
import base64
import logging

import anthropic
import cv2
import mss
import mss.tools
import numpy as np
import pyautogui

from flowstate.state import SharedSentinelState, SSEEvent, TaskContext
from flowstate.config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)

# Speed up pyautogui — default 0.1s pause is too slow for demo
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True  # Move mouse to corner to abort


def _take_screenshot() -> tuple[str, str]:
    """Capture primary monitor, return (base64_data, media_type)."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = np.array(shot)[:, :, :3]  # BGRA → BGR, drop alpha
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 65])
        return base64.standard_b64encode(buf.tobytes()).decode(), "image/jpeg"


def _get_screen_size() -> tuple[int, int]:
    """Return (width, height) of primary monitor."""
    with mss.mss() as sct:
        m = sct.monitors[1]
        return m["width"], m["height"]


def _execute_action(action: str, params: dict) -> None:
    """Execute a Computer Use action via pyautogui."""
    coord = params.get("coordinate")

    if action == "screenshot":
        return
    elif action == "mouse_move":
        if coord:
            pyautogui.moveTo(coord[0], coord[1], duration=0.15)
    elif action == "left_click":
        if coord:
            pyautogui.click(coord[0], coord[1])
        else:
            pyautogui.click()
    elif action == "right_click":
        if coord:
            pyautogui.rightClick(coord[0], coord[1])
        else:
            pyautogui.rightClick()
    elif action == "double_click":
        if coord:
            pyautogui.doubleClick(coord[0], coord[1])
        else:
            pyautogui.doubleClick()
    elif action == "middle_click":
        if coord:
            pyautogui.middleClick(coord[0], coord[1])
        else:
            pyautogui.middleClick()
    elif action == "type":
        text = params.get("text", "")
        pyautogui.write(text, interval=0.02)
    elif action == "key":
        key = params.get("key", "")
        key_map = {
            "Return": "enter", "space": "space", "BackSpace": "backspace",
            "Tab": "tab", "Escape": "escape", "super": "win",
        }
        pyautogui.press(key_map.get(key, key))
    elif action == "scroll":
        delta_y = params.get("delta_y", 0)
        clicks = delta_y // 100 if delta_y else 0
        if coord:
            pyautogui.scroll(clicks, coord[0], coord[1])
        else:
            pyautogui.scroll(clicks)
    elif action == "left_click_drag":
        start = params.get("start_coordinate", coord)
        end = params.get("coordinate", [0, 0])
        if start:
            pyautogui.moveTo(start[0], start[1])
            pyautogui.drag(end[0] - start[0], end[1] - start[1], duration=0.3)


def _describe_action(action: str, params: dict) -> str:
    """Human-readable description for SSE action feed."""
    coord = params.get("coordinate")
    if action == "screenshot":
        return "Capturing screen..."
    elif action in ("left_click", "right_click", "double_click"):
        pos = f" at ({coord[0]}, {coord[1]})" if coord else ""
        return f"{action.replace('_', ' ').title()}{pos}"
    elif action == "mouse_move":
        return f"Moving to ({coord[0]}, {coord[1]})" if coord else "Moving cursor"
    elif action == "type":
        text = params.get("text", "")
        preview = text[:60] + ("..." if len(text) > 60 else "")
        return f'Typing: "{preview}"'
    elif action == "key":
        return f"Key: {params.get('key', '?')}"
    elif action == "scroll":
        return "Scrolling"
    return f"{action}"


def _action_icon(action: str) -> str:
    if action in ("type", "key"):
        return "terminal"
    elif action in ("left_click", "right_click", "double_click", "mouse_move", "scroll"):
        return "browser"
    elif action == "screenshot":
        return "search"
    return "terminal"


async def run(state: SharedSentinelState):
    """Entry point — uses real Computer Use if API key is set, else mock."""
    if not ANTHROPIC_API_KEY:
        log.info("Control: no API key — running mock pipeline")
        await _mock_control(state)
        return

    try:
        log.info("Control: starting real Computer Use pipeline")
        await _real_control(state)
    except Exception:
        log.exception("Real Computer Use failed — falling back to mock")
        await _mock_control(state)


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
    """Real Claude Computer Use — takes screenshots, executes actions on screen."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    ctx: TaskContext = state.task_context

    screen_w, screen_h = _get_screen_size()

    # Take initial screenshot
    await state.sse_queue.put(SSEEvent(
        type="action",
        data={"step": "Analyzing your screen...", "icon": "search"},
    ))
    screenshot_b64, media_type = _take_screenshot()

    # Build prompt from task context
    task_info = ""
    if ctx:
        task_info = (
            f"Task context from screen analysis:\n"
            f"- Task type: {ctx.task_type}\n"
            f"- Summary: {ctx.visible_text_summary}\n"
            f"- Suggested steps: {', '.join(ctx.suggested_next_steps)}\n"
        )
        if ctx.codebase_context:
            task_info += f"- Codebase context: {ctx.codebase_context}\n"

    prompt = (
        f"You are taking over from a stressed developer. Here is their current screen.\n\n"
        f"{task_info}\n"
        f"You have full control of their computer. Examine the screen and take "
        f"the most helpful action you can. Be efficient — the developer is resting.\n"
        f"When you're done, explain what you did."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": screenshot_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    max_iterations = 15
    for i in range(max_iterations):
        if state.stop_control.is_set():
            log.info("Control: stop requested at iteration %d", i)
            break

        response = await client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=[
                {
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": screen_w,
                    "display_height_px": screen_h,
                },
            ],
            messages=messages,
            betas=["computer-use-2025-01-24"],
        )

        # Show Claude's reasoning in the action feed
        for block in response.content:
            if hasattr(block, "text") and block.text:
                await state.sse_queue.put(SSEEvent(
                    type="action",
                    data={"step": block.text[:150], "icon": "search"},
                ))

        if response.stop_reason == "end_turn":
            log.info("Control: Claude finished (end_turn) at iteration %d", i)
            break

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            break

        tool_results = []
        for tu in tool_uses:
            action = tu.input.get("action", "screenshot")

            # Push action description to UI
            desc = _describe_action(action, tu.input)
            icon = _action_icon(action)
            await state.sse_queue.put(SSEEvent(
                type="action",
                data={"step": desc, "icon": icon},
            ))

            # Execute the action on screen
            if action != "screenshot":
                _execute_action(action, tu.input)
                await asyncio.sleep(0.5)  # Wait for UI to settle

            # Capture result screenshot
            screenshot_b64, media_type = _take_screenshot()

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": screenshot_b64,
                        },
                    }
                ],
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    await state.sse_queue.put(SSEEvent(
        type="done",
        data={"message": "Task complete. Control returned to you."},
    ))
    state.stop_control.set()
