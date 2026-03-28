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


async def _main():
    state = init_state()
    set_state(state)

    config = uvicorn.Config(app, host=API_HOST, port=API_PORT, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        webcam_run(state),
        screen_run(state),
        orch_run(state),
        sentiment_run(state),
    )


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
