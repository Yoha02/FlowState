# FlowState — Ambient Stress-Aware Agent

> Watches you work. Takes over when you hit the wall.

FlowState is an ambient developer wellness agent. It monitors your facial expressions via webcam in real-time, detects stress and fatigue using **Gemini 2.0 Flash** vision, and when you cross the threshold — with your consent — **Claude Computer Use** takes over your GCP Cloud Shell to fix the problem while you rest.

## How It Works

```
Webcam (5s tick) → Gemini Flash (sentiment) → State Machine → Consent Modal → Claude Takes Over
```

1. **Webcam capture** — OpenCV grabs frames every 5 seconds (rolling buffer of 5)
2. **Sentiment analysis** — Gemini 2.0 Flash scores each batch for stress + fatigue (0-1)
3. **Threshold detection** — 3 consecutive high-stress readings (15s) triggers the handoff
4. **Consent modal** — You approve or dismiss (30s timeout, auto-dismisses)
5. **Context gathering** — Gemini reads your screen + Augment Code reads your codebase
6. **Autonomous takeover** — Claude Computer Use opens GCP Cloud Shell and fixes the issue
7. **Live feed** — Every agent action streams to the UI in real-time via SSE

## Architecture

```
STREAM A (always on):  webcam → sentiment_agent → score_queue
STREAM B (always on):  screen capture → rolling_buffer

ORCHESTRATOR:          score_queue → state_machine → handoff_trigger

HANDOFF PIPELINE:      negotiator (consent modal)
                       → assessor (Gemini + Augment Code)
                       → control (Claude Computer Use)
                       → done → reset
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Vision | Gemini 2.0 Flash | Facial sentiment + screen context analysis |
| Control | Claude Computer Use | GCP Cloud Shell autonomous operation |
| Context | Augment Code MCP | Codebase understanding when coding task detected |
| Orchestration | Railtracks 1.3.6 | Agent lifecycle + flow visualization |
| Rate Limiting | Unkey | Per-session API key management |
| Backend | FastAPI + SSE | Real-time event bridge |
| Frontend | Next.js + Tailwind 4 | Ambient dashboard (Controlled Chaos design) |
| Deploy | DigitalOcean App Platform | Production hosting |

## Quick Start

### Backend
```bash
cd flowstate
cp .env.example .env   # Fill in your API keys
pip install uv
uv sync
uv run flowstate
```

### Frontend
```bash
cd flowstate/ui
npm install
npm run dev
```

Open http://localhost:3000 — the ambient status bar appears at the top.

## Demo Scenario (3 minutes)

| Time | What Happens |
|------|-------------|
| 0:00-0:25 | Developer debugging broken Cloud Run service. Status bar: green → yellow → red |
| 0:25-0:45 | Threshold hit. Consent modal: "Want me to take over?" → User approves |
| 0:45-1:05 | Gemini reads screen + Augment Code reads codebase (parallel) |
| 1:05-2:10 | Claude opens Cloud Shell, reads logs, fixes env var, redeploys |
| 2:10-2:40 | Proof: service healthy, Railtracks viz, Unkey dashboard |
| 2:40-3:00 | "Want to try it on your own service?" |

## SSE Event Contract

```jsonc
// Status updates (continuous)
{"type": "status_update", "data": {"state": "calm|elevated|stressed|critical", "consecutive": 2, "stress": 0.7, "fatigue": 0.6}}

// Handoff trigger (when threshold crossed)
{"type": "handoff_trigger", "data": {"evidence": "...", "task_summary": "..."}}

// Agent actions (during takeover)
{"type": "action", "data": {"step": "Running gcloud...", "icon": "terminal|browser|search|check"}}

// Completion
{"type": "done", "data": {"message": "Task complete. Control returned to you."}}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STRESS_THRESHOLD` | 3 | Consecutive stressed frames before handoff |
| `TICK_WEBCAM_SECONDS` | 5 | Webcam capture interval |
| `TICK_SCREEN_SECONDS` | 15 | Screen capture interval |
| `HANDOFF_TIMEOUT_SECONDS` | 30 | Consent modal timeout |

## License

Built for the Multimodal Frontier Hackathon, March 2026.
