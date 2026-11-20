"""Shared, long-lived HTTP client for LLM adapters.

Constructing httpx.AsyncClient performs synchronous TLS and CA-bundle setup (~300 ms
measured on Windows). Building one per call blocked the event loop under load, so
adapters reuse one pooled client per running event loop instead.
"""

import asyncio
from typing import Any

import httpx

_clients: dict[int, httpx.AsyncClient] = {}


def shared_async_client() -> httpx.AsyncClient:
    """Return the pooled client for the running event loop, creating it once."""
    key = id(asyncio.get_running_loop())
    client = _clients.get(key)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        _clients[key] = client
    return client


def reset_shared_clients() -> None:
    """Forget cached clients (tests; clients of finished loops are not reused)."""
    _clients.clear()


async def post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.Response:
    """POST JSON with the shared client, or a one-off client when a transport is injected."""
    if transport is not None:  # tests inject a mock transport
        async with httpx.AsyncClient(transport=transport) as client:
            return await client.post(url, headers=headers, json=payload, timeout=timeout)
    return await shared_async_client().post(url, headers=headers, json=payload, timeout=timeout)
