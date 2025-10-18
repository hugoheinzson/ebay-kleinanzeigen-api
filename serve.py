import logging
import os
import threading

import uvicorn

from main import app as api_app
from mcp_server import create_mcp_server


def _start_mcp_server() -> None:
    logger = logging.getLogger(__name__)
    try:
        server = create_mcp_server()
        logger.info("Starting MCP server on %s:%s", server.settings.host, server.settings.port)
        server.run("streamable-http")
    except Exception as exc:  # pragma: no cover - log unexpected startup failures
        logger.exception("MCP server stopped unexpectedly: %s", exc)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    mcp_thread = threading.Thread(target=_start_mcp_server, daemon=True, name="mcp-server")
    mcp_thread.start()

    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    try:
        uvicorn.run(api_app, host=api_host, port=api_port, log_level=os.getenv("UVICORN_LOG_LEVEL", "info"))
    finally:
        if mcp_thread.is_alive():
            logging.getLogger(__name__).info("Waiting for MCP server thread to exit")
            mcp_thread.join(timeout=5)


if __name__ == "__main__":
    main()
