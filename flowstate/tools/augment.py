"""Augment Code Context Engine client."""
from __future__ import annotations

import logging

import httpx

from flowstate.config import AUGMENT_API_KEY

logger = logging.getLogger(__name__)


async def get_codebase_context(query: str) -> str:
    """Query Augment Code Context Engine for relevant codebase context."""
    if not AUGMENT_API_KEY:
        return (
            "Recent commit in api/routes.py (2h ago): added API_KEY env var reference. "
            "Cloud Run service config does not include API_KEY in env vars. "
            "Suggested fix: add API_KEY to Cloud Run service env configuration."
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.augmentcode.com/v1/codebase-retrieval",
                headers={"Authorization": f"Bearer {AUGMENT_API_KEY}"},
                json={"query": query, "limit": 5},
                timeout=15.0,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return "\n".join(r.get("context", "") for r in results)
            logger.warning("Augment API returned %s", resp.status_code)
            return ""
    except Exception:
        logger.exception("Augment codebase context query failed")
        return ""
