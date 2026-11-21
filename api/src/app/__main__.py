"""Windows-compatible entrypoint for running the API locally with psycopg async."""

import asyncio
import os
import selectors
import sys

import uvicorn


def main() -> None:
    """Start Uvicorn (selector loop on Windows) on API_HOST:API_PORT, default 127.0.0.1:8000."""
    config = uvicorn.Config(
        "app.main:app",
        host=os.environ.get("API_HOST", "127.0.0.1"),
        port=int(os.environ.get("API_PORT", "8000")),
    )
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        asyncio.run(
            server.serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()
