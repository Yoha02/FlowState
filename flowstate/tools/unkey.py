"""Async rate gate using Unkey API."""
from __future__ import annotations

import logging

import httpx

from flowstate.config import UNKEY_ROOT_KEY, UNKEY_API_ID

logger = logging.getLogger(__name__)

# Rate limit configs per namespace
_LIMITS: dict[str, dict] = {
    "flowstate-sentiment": {"limit": 12, "duration": 60_000},   # 12 req/min
    "flowstate-screen":    {"limit": 10, "duration": 3_600_000}, # 10 req/hour
}


async def check_rate_limit(namespace: str) -> bool:
    """Returns True if call is allowed, False if rate limited."""
    if not UNKEY_ROOT_KEY:
        return True  # dev mode bypass

    cfg = _LIMITS.get(namespace, {"limit": 10, "duration": 60_000})

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.unkey.dev/v1/ratelimits.limit",
                headers={
                    "Authorization": f"Bearer {UNKEY_ROOT_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "namespace": namespace,
                    "identifier": "flowstate",
                    "limit": cfg["limit"],
                    "duration": cfg["duration"],
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("success", True)
            logger.warning("Unkey rate limit check returned %s", resp.status_code)
            return True  # fail open
    except Exception:
        logger.exception("Unkey rate limit check failed")
        return True  # fail open


async def verify_key(key: str) -> bool:
    """Verify an API key is valid via Unkey."""
    if not UNKEY_ROOT_KEY:
        return True  # dev mode bypass

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.unkey.dev/v1/keys.verifyKey",
                headers={
                    "Content-Type": "application/json",
                },
                json={"apiId": UNKEY_API_ID, "key": key},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("valid", False)
            return False
    except Exception:
        logger.exception("Unkey key verification failed")
        return False
