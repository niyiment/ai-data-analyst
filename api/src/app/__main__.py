"""Windows-compatible entrypoint for running the API locally with psycopg async."""

import asyncio
import selectors
import sys

import uvicorn


def main() -> None:
    """Start the Uvicorn server using SelectorEventLoop on Windows."""
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000)
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
