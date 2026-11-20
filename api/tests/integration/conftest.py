"""Integration tests run only when the local PostgreSQL from docker compose is reachable."""

import asyncio
import selectors
from collections.abc import Callable, Mapping

import psycopg
import pytest

from app.core.config import get_settings


def _selector_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.DefaultSelector())


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    """psycopg async cannot use Windows' default Proactor loop; a selector loop works everywhere."""
    return {"selector": _selector_loop}


def _database_reachable() -> bool:
    dsn = get_settings().database_url_analyst.replace("postgresql+psycopg://", "postgresql://")
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            return True
    except psycopg.OperationalError:
        return False


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if _database_reachable():
        return
    skip = pytest.mark.skip(reason="PostgreSQL not reachable (run: docker compose up -d postgres)")
    for item in items:
        if "tests/integration" in item.nodeid.replace("\\", "/"):
            item.add_marker(skip)
