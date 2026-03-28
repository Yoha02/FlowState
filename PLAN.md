# FlowState — Project Plan

> Ambient stress-aware agent that watches you work, detects fatigue/stress via webcam,
> and takes over your GCP terminal when you hit the wall.

---

## Elevator Pitch

"FlowState watches your face while you work. When you're stressed or exhausted,
it asks if you want help — then reads your codebase, opens your GCP Cloud Shell,
and fixes the problem while you rest."

---

## Demo Scenario (3 minutes, optimised for judges)

```
[0:00–0:25]  Developer debugging a broken Cloud Run service.
             Status bar: green → yellow → red (stress climbing live).

[0:25–0:45]  Threshold hit (3 consecutive stressed frames = 15s).
             HandoffModal appears (assistant-ui tool call):
             "You've looked stressed for 15 seconds.
              I can see your Cloud Run service is unhealthy.
              Want me to take over?"  [Take Over]  [Not now]
             → User clicks Take Over and steps back.

[0:45–1:05]  Two agents fire in parallel (show Railtracks viz):
             - Gemini 3 Flash: reads screenshot → identifies service + error type
             - Augment Code MCP: queries repo → finds recent commit that broke env var

[1:05–2:10]  Claude Computer Use opens GCP Cloud Shell (visible browser).
             ActionFeed logs each step live:
               "Reading Cloud Run logs..."
               gcloud logging read "resource.type=cloud_run_revision" --limit=20
               "Confirmed: Missing API_KEY environment variable"
               gcloud run services update SERVICE --set-env-vars API_KEY=***
               "Redeployment triggered..."
               "✓ Service healthy. 0 errors in last 60 seconds."

[2:10–2:40]  Proof panel:
             - Railtracks viz: full agent decision graph
             - GCP Cloud Run: green status
             - Unkey dashboard: live API call usage visible

[2:40–3:00]  "Want to try it on your own service?"
             → Hand laptop to judge (Bharat Bhavnasi moment)
```

---

## Prize Tracks

| Track | Prize | How We Win |
|---|---|---|
| Railtracks | $1,300 cash (3 winners) | Hero orchestration framework — all agents run through Railtracks Flow |
| Augment Code | $3,500 cash (3 winners) | Context Engine reads repo when stress detected — natural, essential, not bolted on |
| DigitalOcean | $1,000 + credits (3 winners) | Deploy FlowState backend on App Platform; route Gemini inference through Gradient |
| assistant-ui | $800 cash (1 winner) | HandoffModal + StatusBar + ActionFeed as tool-call-driven UI components |
| Unkey | $25k value (1 winner) | Per-session keys + rate-limit every Gemini call; show live Unkey dashboard |

**3 required sponsor tools:** Railtracks + Gemini (Google DeepMind) + assistant-ui ✓

---

## Services & API Keys (Get Before Hackathon)

| Service | What For | Where to Get | Key Name in .env |
|---|---|---|---|
| Google AI Studio | Gemini 3 Flash — sentiment + task context | aistudio.google.com | `GEMINI_API_KEY` |
| Anthropic API | Claude Computer Use — browser/terminal control | console.anthropic.com | `ANTHROPIC_API_KEY` |
| Augment Code | Context Engine MCP — codebase understanding | app.augmentcode.com | `AUGMENT_API_KEY` |
| Unkey | API key management + rate limiting | unkey.dev | `UNKEY_ROOT_KEY`, `UNKEY_API_ID` |
| DigitalOcean | App Platform deploy + Gradient inference | cloud.digitalocean.com | `DO_API_KEY`, `DO_GRADIENT_BASE_URL` |
| Shipables.dev | Mandatory skill submission | shipables.dev | (CLI auth, no key) |
| GitHub | Demo target repo (the broken Cloud Run app) | github.com | `GITHUB_TOKEN` (optional) |

---

## assistant-ui Interactables — Our 4 Components

assistant-ui's tool-call UI system lets the AI trigger and update React components
outside the chat thread. We register 4 tool-callable components:

### 1. SentinelStatusBar
- Thin ambient strip at top of screen
- AI calls `update_stress_status` tool → updates color + label
- States: CALM (green) → ELEVATED (yellow) → STRESSED (orange) → CRITICAL (pulsing red)

### 2. HandoffModal  ← The money moment
- Full-screen overlay with consent prompt
- AI calls `trigger_handoff` tool with evidence summary
- Renders: stress evidence + "Want me to take over?" + [Take Over] [Not now] + 30s countdown
- User response POSTs back to Python backend → sets handoff_approved event

### 3. TaskContextCard
- Appears after user approves
- AI calls `set_task_context` tool with Gemini + Augment analysis
- Renders: what you were working on, which file/service, what the agent plans to do

### 4. ActionFeed
- Live scrolling log of agent actions during takeover
- AI calls `append_action` tool for each step
- Each entry: icon + description + timestamp
- Kill-switch button at top: "Take back control" → sends STOP to backend

---

## Shipables.dev Submission

**This is mandatory. Do it at 3:00 PM, not 4:25 PM.**

### SKILL.md (create this at 3:00 PM)
```yaml
---
name: flowstate-sentinel
description: Ambient stress detection agent that monitors developer fatigue
             via webcam and autonomously takes over GCP/browser tasks when
             stress threshold is crossed. Powered by Gemini 3 Flash + Railtracks.
---
```

### Publish steps
```bash
# Install CLI
npm install -g @senso-ai/shipables

# Login
npx @senso-ai/shipables login

# From project root (SKILL.md must exist)
npx @senso-ai/shipables publish

# Verify it's live
npx @senso-ai/shipables info <username>/flowstate-sentinel
```

---

## Full Tech Stack

### Backend (Python 3.11+)
```
railtracks>=1.3.6          # Agent orchestration, Flow, viz
google-generativeai        # Gemini 3 Flash — sentiment + task context
anthropic                  # Claude Computer Use — terminal/browser control
opencv-python              # Webcam capture (cv2.VideoCapture)
pyautogui                  # Screen capture fallback
mss                        # Fast cross-platform screenshots
playwright                 # Browser automation fallback (GitHub path)
fastapi                    # Backend API server
uvicorn                    # ASGI server
unkey                      # Rate limiting wrapper
asyncio                    # Concurrent agent loops (built-in)
python-dotenv              # .env loading
```

### Frontend (TypeScript / Next.js)
```
next                       # Framework
@assistant-ui/react        # Chat + tool-call UI components
@assistant-ui/react-ai-sdk # Vercel AI SDK bridge
ai                         # Vercel AI SDK (streaming)
tailwindcss                # Styling
```

### Infrastructure
```
DigitalOcean App Platform  # Host Python backend
Vercel                     # Host Next.js frontend (faster deploy)
Unkey                      # API key management (SaaS)
Augment Code MCP           # Remote MCP server (no self-hosting needed)
```

---

## Project Structure

```
flowstate/
├── .env.example               # All required keys documented
├── SKILL.md                   # Shipables.dev submission (create at 3PM)
├── README.md                  # GitHub repo (required for Devpost)
├── pyproject.toml             # Python deps (uv-compatible)
│
├── flowstate/                 # Python package
│   ├── __init__.py
│   ├── config.py              # STRESS_THRESHOLD=3, TICK_WEBCAM=5, TICK_SCREEN=15
│   ├── state.py               # SharedSentinelState, SentimentScore, TaskContext dataclasses
│   ├── main.py                # asyncio.gather boot — starts all loops
│   │
│   ├── streams/
│   │   ├── webcam_monitor.py  # OpenCV, 5s tick, deque(maxlen=5)
│   │   └── screen_context.py  # pyautogui/mss, rolling context buffer
│   │
│   ├── agents/
│   │   ├── sentiment.py       # Gemini 3 Flash vision → SentimentScore
│   │   ├── orchestrator.py    # State machine: CALM→ELEVATED→STRESSED→CRITICAL
│   │   ├── negotiator.py      # Fires HandoffModal via UI bridge, waits for response
│   │   ├── assessor.py        # Gemini + Augment Code → TaskContext
│   │   └── control.py        # Claude Computer Use → GCP Cloud Shell actions
│   │
│   ├── tools/
│   │   ├── unkey.py           # async rate gate (flowstate-sentiment, flowstate-screen namespaces)
│   │   ├── gemini.py          # Vision call wrapper (frames → SentimentScore)
│   │   ├── augment.py         # Augment Code MCP client
│   │   └── computer_use.py    # Anthropic computer use wrapper
│   │
│   └── api/
│       ├── server.py          # FastAPI app
│       ├── sse.py             # SSE stream → frontend status updates
│       └── routes.py          # POST /handoff/respond, GET /status/stream
│
└── ui/                        # Next.js frontend
    ├── package.json
    ├── app/
    │   ├── layout.tsx
    │   └── page.tsx           # Root — mounts all 4 Interactable components
    └── components/
        ├── SentinelStatusBar.tsx   # Tool: update_stress_status
        ├── HandoffModal.tsx        # Tool: trigger_handoff
        ├── TaskContextCard.tsx     # Tool: set_task_context
        └── ActionFeed.tsx          # Tool: append_action + kill-switch
```

---

## Agent Topology (Railtracks)

```
STREAM A (always on, 5s tick):
  webcam_monitor → [buffer full] → sentiment_agent → score_queue

STREAM B (always on, 15s tick):
  screen_context → rolling_buffer (passive)

ORCHESTRATOR (always on, drains score_queue):
  score_queue → state_machine → [threshold=3] → handoff_trigger

HANDOFF PIPELINE (triggered, sequential):
  handoff_trigger
    → negotiator_agent      (fires HandoffModal, waits ≤30s)
    → [approved]
    → assessor_agent        (Gemini + Augment Code, parallel)
    → control_agent         (Claude Computer Use, GCP Cloud Shell)
    → [done/stop/error]
    → reset state, resume streams
```

**Concurrency model:**
- Streams A + B + Orchestrator: `asyncio.gather` — always running concurrently
- Handoff pipeline: sequential chain — each step awaits the prior
- assessor_agent: Gemini call + Augment call run in parallel via `asyncio.gather`

---

## Team Build Order (5.5 hours)

### Pre-Hackathon (Do Tonight)
- [ ] Get all API keys (see Services table above)
- [ ] Test `cv2.VideoCapture(0)` works on the demo machine
- [ ] `railtracks viz` running locally
- [ ] `npx @senso-ai/shipables login` auth done
- [ ] Next.js scaffold with assistant-ui installed
- [ ] Demo repo on GitHub (broken Cloud Run app) ready to use as test target

### Hour 0–1.5: Foundation (all 4 in parallel)
- **A**: `state.py` + `webcam_monitor.py` + `screen_context.py` + `main.py` boot loop
- **B**: `negotiator.py` shell + `assessor.py` shell (ResultCapture pattern from bob)
- **C**: `sentiment.py` (Gemini vision call) + `unkey.py` (rate gate)
- **D**: Next.js scaffold, `SentinelStatusBar.tsx` + SSE listener wired

### Hour 1.5–3.0: Core Agents
- **A**: `orchestrator.py` state machine, wires score_queue → handoff_trigger
- **B**: `control.py` (Claude Computer Use, Cloud Shell gcloud commands)
- **C**: Frame batching + Augment Code MCP client (`augment.py`)
- **D**: `HandoffModal.tsx` (Interactable) + POST /handoff/respond backend route

### Hour 3.0–4.5: Integration
- Full pipeline test: webcam → sentiment → state machine → modal → approve → Cloud Shell
- Tune Gemini stress/fatigue prompt with real faces
- `ActionFeed.tsx` wired to live SSE stream
- DigitalOcean App Platform deploy (Person A)

### 3:00 PM — FEATURE FREEZE ⚠️
No new features. Cut anything not working. Ship what works.

### 3:00 PM — SHIPABLES (Person D)
Write `SKILL.md` → `npx @senso-ai/shipables publish` → verify live.

### 3:00–4:00 PM: Polish + Submission
- Record 3-min demo video (screen + voiceover)
- GitHub repo README with architecture diagram
- Devpost submission: all fields, GitHub link, video, sponsor tools listed
- Verify Devpost is SUBMITTED (not draft)

### 4:00–4:30 PM: Demo Rehearsal
- Full 3-min run × 3 with stopwatch
- Practice 3-sec / 30-sec / 90-sec versions
- Pre-load demo: broken Cloud Run app URL ready, Augment Code repo indexed

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Claude Computer Use slow on Windows | Medium | Test latency before demo; pre-stage Cloud Shell tab open |
| Gemini stress detection noisy | High | Tune prompt with rubric; manual override in config.py |
| Augment Code indexing takes too long | Low | Index demo repo tonight, keep it open during hackathon |
| Shipables publish fails last minute | Medium | Do at 3:00 PM sharp, not 4:25 PM |
| GCP Cloud Shell session expires | Medium | Keep Cloud Shell tab open and active during demo |
| assistant-ui Interactable not working | Medium | Fallback: plain React state + useEffect for modal trigger |
| Unkey rate limiting too aggressive | Low | Set 15 req/min limit (not 12), test before demo |

---

## .env.example

```bash
# Google AI — Gemini 3 Flash (sentiment + task context)
GEMINI_API_KEY=

# Anthropic — Claude Computer Use (terminal/browser takeover)
ANTHROPIC_API_KEY=

# Augment Code — Context Engine MCP
AUGMENT_API_KEY=

# Unkey — API key management + rate limiting
UNKEY_ROOT_KEY=
UNKEY_API_ID=

# DigitalOcean — App Platform + Gradient inference
DO_API_KEY=
DO_GRADIENT_BASE_URL=https://inference.do-ai.run/v1

# App config
STRESS_THRESHOLD=3
TICK_WEBCAM_SECONDS=5
TICK_SCREEN_SECONDS=15
HANDOFF_TIMEOUT_SECONDS=30

# Demo target (Cloud Run service to fix)
DEMO_GCP_PROJECT=
DEMO_CLOUD_RUN_SERVICE=
```
