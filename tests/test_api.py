"""Tests for FastAPI endpoints."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from flowstate.api.server import app, set_state
from flowstate.state import init_state


@pytest.fixture
def client():
    state = asyncio.run(_make_state())
    set_state(state)
    return TestClient(app)


async def _make_state():
    return init_state()


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_handoff_respond_reject(client):
    resp = client.post(
        "/handoff/respond",
        json={"approved": False},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_handoff_respond_approve(client):
    resp = client.post(
        "/handoff/respond",
        json={"approved": True},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
