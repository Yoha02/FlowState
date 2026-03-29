"""Computer control agent — Claude Computer Use takes over the user's screen.

Two-phase approach:
  Phase 1: Claude analyzes the screen and proposes a plan (no actions)
  Phase 2: After user confirms, Claude executes the plan with real actions
"""

import asyncio
import base64
import logging

import anthropic
import cv2
import mss
import mss.tools
import numpy as np
import pyautogui
import pyperclip

from flowstate.state import SharedSentinelState, SSEEvent, TaskContext
from flowstate.config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)

# Speed up pyautogui
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True  # Move mouse to corner to abort

# Downscale target — makes UI elements appear larger to Claude's vision
# so it can identify and target them more accurately with the mouse.
SCREENSHOT_TARGET_WIDTH = 1280


def _take_screenshot() -> tuple[str, str, int, int, float, float]:
    """Capture primary monitor, downscale for Claude, return
    (base64_data, media_type, scaled_w, scaled_h, scale_x, scale_y).

    scale_x/scale_y convert from downscaled coords → real screen coords.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = np.array(shot)[:, :, :3]
        real_h, real_w = img.shape[:2]

        # Downscale so UI elements look bigger to the model
        if real_w > SCREENSHOT_TARGET_WIDTH:
            ratio = SCREENSHOT_TARGET_WIDTH / real_w
            new_w = SCREENSHOT_TARGET_WIDTH
            new_h = int(real_h * ratio)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            new_w, new_h = real_w, real_h

        scale_x = real_w / new_w
        scale_y = real_h / new_h

        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.standard_b64encode(buf.tobytes()).decode()
        return b64, "image/jpeg", new_w, new_h, scale_x, scale_y


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
    elif action == "type":
        text = params.get("text", "")
        # Clipboard paste — instant, handles all characters
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
    elif action == "key":
        key = params.get("key", "")
        key_map = {
            "Return": "enter", "space": "space", "BackSpace": "backspace",
            "Tab": "tab", "Escape": "escape", "super": "win",
            "Control_L": "ctrl", "Control_R": "ctrl", "Alt_L": "alt",
            "Shift_L": "shift", "Shift_R": "shift",
        }
        # Support combos like "ctrl+c", "ctrl+l", "ctrl+a"
        if not key:
            log.warning("Control: empty key — skipping")
            return
        parts = [p.strip() for p in key.replace("+", " ").split() if p.strip()]
        mapped = [key_map.get(p, p.lower()) for p in parts]
        if not mapped:
            log.warning("Control: no valid keys from '%s' — skipping", key)
            return
        if len(mapped) > 1:
            pyautogui.hotkey(*mapped)
        else:
            pyautogui.press(mapped[0])
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
    coord = params.get("coordinate")
    if action == "screenshot":
        return "Capturing screen..."
    elif action in ("left_click", "right_click", "double_click"):
        pos = f" at ({coord[0]}, {coord[1]})" if coord else ""
        return f"{action.replace('_', ' ').title()}{pos}"
    elif action == "mouse_move":
        return f"Moving to ({coord[0]}, {coord[1]})" if coord else "Moving cursor"
    elif action == "type":
        preview = params.get("text", "")[:60]
        return f'Typing: "{preview}"'
    elif action == "key":
        return f"Key: {params.get('key', '?')}"
    elif action == "scroll":
        return "Scrolling"
    return action


def _action_icon(action: str) -> str:
    if action in ("type", "key"):
        return "terminal"
    elif action in ("left_click", "right_click", "double_click", "mouse_move", "scroll"):
        return "browser"
    return "search"


async def run(state: SharedSentinelState):
    if not ANTHROPIC_API_KEY:
        log.info("Control: no API key — running mock pipeline")
        await _mock_control(state)
        return

    try:
        log.info("Control: starting real Computer Use pipeline")
        await _real_control(state)
    except Exception:
        log.exception("Real Computer Use failed")
        await state.sse_queue.put(SSEEvent(
            type="action",
            data={"step": "Error: Computer Use failed — check logs", "icon": "search"},
        ))
        await state.sse_queue.put(SSEEvent(
            type="done",
            data={"message": "Agent encountered an error. Control returned to you."},
        ))
        state.stop_control.set()


async def _mock_control(state: SharedSentinelState):
    """Demo-safe mock that pushes realistic action steps."""
    await asyncio.sleep(1.0)
    await state.sse_queue.put(SSEEvent(
        type="plan_proposal",
        data={
            "plan": (
                "I can see you have GCP Cloud Shell open with project multimodal-491620.\n\n"
                "Here's what I'll do:\n"
                "1. Check Cloud Run service logs for recent errors\n"
                "2. Identify the root cause (likely a missing environment variable)\n"
                "3. Update the service configuration to fix the issue\n"
                "4. Verify the service is healthy"
            ),
        },
    ))
    await state.plan_confirmed.wait()
    state.plan_confirmed.clear()

    steps = [
        ("Running: gcloud logging read --limit=20", "terminal"),
        ("Found error: KeyError 'API_KEY' in main.py line 42", "search"),
        ("Running: gcloud run services update demo-svc --set-env-vars API_KEY=***", "terminal"),
        ("Waiting for deployment to complete...", "browser"),
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
    """Real Claude Computer Use — two-phase: plan then execute."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    ctx: TaskContext = state.task_context

    # ── Phase 1: Analyze & Plan (no tool use) ──
    await state.sse_queue.put(SSEEvent(
        type="action",
        data={"step": "Analyzing your screen...", "icon": "search"},
    ))

    screenshot_b64, media_type, _, _, _, _ = _take_screenshot()

    task_info = ""
    if ctx:
        task_info = (
            f"Task context:\n"
            f"- Type: {ctx.task_type}\n"
            f"- Summary: {ctx.visible_text_summary}\n"
            f"- Suggested: {', '.join(ctx.suggested_next_steps)}\n"
        )
        if ctx.codebase_context:
            task_info += f"- Codebase: {ctx.codebase_context}\n"

    plan_response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": screenshot_b64},
                },
                {
                    "type": "text",
                    "text": (
                        f"You are an AI assistant taking over from a stressed developer. Look at their screen carefully.\n\n"
                        f"{task_info}\n"
                        f"Analyze what you see and propose a clear action plan.\n"
                        f"Format:\n"
                        f"1. What you observe on screen (read ALL text including error messages)\n"
                        f"2. What problem needs solving (be specific — quote the error)\n"
                        f"3. Your step-by-step plan (3-5 concrete steps)\n\n"
                        f"NAVIGATION RULES:\n"
                        f"- To navigate to a URL: press Ctrl+L to focus the address bar, then type the URL and press Enter\n"
                        f"- To enable a GCP API: navigate to the API's page in the API Library and click the Enable button\n"
                        f"- For Kubernetes Engine: navigate to console.cloud.google.com/apis/library/container.googleapis.com\n"
                        f"- Click on LARGE, obvious buttons and links — avoid tiny icons\n"
                        f"- Use the Navigation Menu (☰ hamburger icon, top-left corner) for GCP console navigation\n"
                        f"- Always verify what happened after each click before proceeding\n\n"
                        f"Do NOT take any actions yet — just analyze and plan."
                    ),
                },
            ],
        }],
    )

    plan_text = plan_response.content[0].text
    log.info("Control Phase 1: Plan proposed — %s", plan_text[:200])

    await state.sse_queue.put(SSEEvent(
        type="plan_proposal",
        data={"plan": plan_text},
    ))

    # Wait for user confirmation
    log.info("Control: waiting for plan confirmation...")
    await state.plan_confirmed.wait()
    state.plan_confirmed.clear()
    log.info("Control: plan confirmed — starting execution")

    # ── Phase 2: Execute with Computer Use ──
    screenshot_b64, media_type, img_w, img_h, scale_x, scale_y = _take_screenshot()

    log.info("Control: screenshot=%dx%d  scale=%.2fx%.2f → real screen",
             img_w, img_h, scale_x, scale_y)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": screenshot_b64},
                },
                {
                    "type": "text",
                    "text": (
                        f"The user has confirmed your plan. Execute it now.\n\n"
                        f"Your plan was:\n{plan_text}\n\n"
                        f"You have full mouse and keyboard control.\n\n"
                        f"EXECUTION RULES:\n"
                        f"- To navigate to a URL: press key combo Ctrl+L to focus the address bar, type the URL, press Enter. NEVER click the address bar with the mouse.\n"
                        f"- Click on LARGE buttons and obvious UI elements. Aim for the CENTER of buttons.\n"
                        f"- After each action, take a screenshot to verify the result before continuing.\n"
                        f"- If you need to enable a GCP API, navigate to its page and click the big blue Enable button.\n"
                        f"- Use the Navigation Menu (☰ hamburger, top-left) to navigate between GCP services.\n"
                        f"- If something doesn't work after 2 tries, try a completely different approach.\n"
                        f"- When done, take a final screenshot to confirm success."
                    ),
                },
            ],
        }
    ]

    max_iterations = 20
    for i in range(max_iterations):
        if state.stop_control.is_set():
            log.info("Control: stop requested at iteration %d", i)
            break

        response = await client.beta.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=[
                {
                    "type": "computer_20251124",
                    "name": "computer",
                    "display_width_px": img_w,
                    "display_height_px": img_h,
                    "enable_zoom": True,
                },
            ],
            messages=messages,
            betas=["computer-use-2025-11-24"],
        )

        # Show Claude's reasoning
        for block in response.content:
            if hasattr(block, "text") and block.text:
                await state.sse_queue.put(SSEEvent(
                    type="action",
                    data={"step": block.text[:150], "icon": "search"},
                ))

        if response.stop_reason == "end_turn":
            log.info("Control: Claude finished at iteration %d", i)
            break

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            break

        tool_results = []
        for tu in tool_uses:
            action = tu.input.get("action", "screenshot")

            # Scale coordinates from downscaled → real screen coords
            params = dict(tu.input)
            if "coordinate" in params and params["coordinate"]:
                cx, cy = params["coordinate"]
                params["coordinate"] = [int(cx * scale_x), int(cy * scale_y)]
                log.info("Control: %s coord (%d,%d) → real (%d,%d)",
                         action, cx, cy, params["coordinate"][0], params["coordinate"][1])
            if "start_coordinate" in params and params["start_coordinate"]:
                sx, sy = params["start_coordinate"]
                params["start_coordinate"] = [int(sx * scale_x), int(sy * scale_y)]

            desc = _describe_action(action, params)
            icon = _action_icon(action)
            await state.sse_queue.put(SSEEvent(
                type="action",
                data={"step": desc, "icon": icon},
            ))

            if action != "screenshot":
                _execute_action(action, params)
                await asyncio.sleep(0.8)  # Extra wait for page loads

            screenshot_b64, media_type, _, _, _, _ = _take_screenshot()

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": screenshot_b64},
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
