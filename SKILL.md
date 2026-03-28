---
name: flowstate-sentinel
description: Ambient stress detection agent that monitors developer fatigue via webcam and autonomously takes over GCP Cloud Shell or browser tasks when stress threshold is crossed. Powered by Gemini 3 Flash vision, Railtracks orchestration, and Augment Code codebase context.
---

# FlowState Sentinel Skill

FlowState is an ambient developer wellness agent. It runs continuously in the background,
monitors the developer's facial expressions via webcam every 5 seconds, and offers to take
over their current task when stress or fatigue is detected.

## What This Skill Does

1. Captures webcam frames every 5 seconds (rolling buffer of 5)
2. Analyses frames with Gemini 3 Flash for stress and fatigue signals
3. When 3 consecutive stressed frames are detected (15 seconds), prompts the user
4. If approved, analyses the current screen context + codebase via Augment Code
5. Uses Claude Computer Use to take over GCP Cloud Shell, browser, or IDE
6. Reports actions live via assistant-ui ActionFeed
7. Returns control to the user when complete or on demand

## Usage

Start the sentinel:
```bash
cd flowstate
uv run python -m flowstate.main
```

The frontend runs separately:
```bash
cd flowstate/ui
npm run dev
```

Open http://localhost:3000 — the ambient status bar will appear at the top of the screen.

## Configuration

Set `STRESS_THRESHOLD` (default: 3 consecutive frames) and `TICK_WEBCAM_SECONDS`
(default: 5) in `.env` to adjust sensitivity.

## Requirements

- Webcam access
- Google AI API key (Gemini 3 Flash)
- Anthropic API key (Claude Computer Use)
- Augment Code API key (Context Engine)
- Unkey account (rate limiting)
