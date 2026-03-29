"""FlowState entrypoint — boots all agents and the API server."""

import asyncio
import logging

import uvicorn

from flowstate.state import init_state
from flowstate.streams.webcam_monitor import run as webcam_run
from flowstate.streams.screen_context import run as screen_run
from flowstate.agents.orchestrator import run as orch_run
from flowstate.agents.sentiment import run as sentiment_run
from flowstate.api.server import app, set_state
from flowstate.config import API_HOST, API_PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def _guarded(name: str, fn, state):
    """Run an agent function forever, restarting on crash."""
    while True:
        try:
            await fn(state)
            return  # normal exit
        except Exception:
            log.exception("%s crashed — restarting in 3s", name)
            await asyncio.sleep(3)


async def _main():
    state = init_state()
    set_state(state)

    config = uvicorn.Config(app, host=API_HOST, port=API_PORT, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        _guarded("webcam", webcam_run, state),
        _guarded("screen", screen_run, state),
        _guarded("orchestrator", orch_run, state),
        _guarded("sentiment", sentiment_run, state),
    )


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
