#!/usr/bin/env python
"""
Unified Odoo MCP Server Runner
Supports both stdio (Claude Desktop) and SSE (Zeabur/Web) transports
"""
import sys
import os
import asyncio
import logging
import datetime
from typing import Optional

# Determine transport mode from environment or command line
TRANSPORT_MODE = os.getenv("MCP_TRANSPORT", "stdio")  # stdio or sse

if TRANSPORT_MODE == "stdio":
    from mcp.server.stdio import stdio_server
elif TRANSPORT_MODE != "sse":
    raise ValueError(f"Invalid MCP_TRANSPORT: {TRANSPORT_MODE}. Must be 'stdio' or 'sse'")

from odoo_mcp.server import mcp


def setup_logging():
    """Set up logging to both console and file"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"mcp_server_{timestamp}.log")

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Format for both handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


async def run_stdio_server(logger):
    """Run server in stdio mode (for Claude Desktop)"""
    logger.info("Starting Odoo MCP server with stdio transport...")

    async with stdio_server() as streams:
        logger.info("Stdio server initialized, running MCP server...")
        await mcp._mcp_server.run(
            streams[0],
            streams[1],
            mcp._mcp_server.create_initialization_options()
        )


async def run_sse_server(logger):
    """Run server in SSE mode (for Zeabur/Web deployment)"""
    logger.info("Starting Odoo MCP server with SSE transport...")

    # Get port from environment
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"SSE server starting on {host}:{port}")
    logger.info(f"SSE endpoint: http://{host}:{port}/sse")

    # Use FastMCP's run_sse_async method
    # Based on actual FastMCP 2.12.4 available methods from Zeabur logs:
    # ['run', 'run_sse_async', 'run_stdio_async', 'run_streamable_http_async']
    await mcp.run_sse_async(
        host=host,
        port=port,
        log_level="info"
    )


def main() -> int:
    """Main entry point"""
    logger = setup_logging()

    try:
        logger.info("=== ODOO MCP UNIFIED SERVER STARTING ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Transport mode: {TRANSPORT_MODE}")

        # Log package versions
        try:
            import fastmcp
            logger.info(f"FastMCP version: {fastmcp.__version__ if hasattr(fastmcp, '__version__') else 'unknown'}")
            logger.info(f"FastMCP location: {fastmcp.__file__}")
            logger.info(f"FastMCP available methods: {[m for m in dir(mcp) if m.startswith('run')]}")
        except Exception as e:
            logger.warning(f"Could not get FastMCP version: {e}")

        try:
            import mcp as mcp_sdk
            logger.info(f"MCP SDK version: {mcp_sdk.__version__ if hasattr(mcp_sdk, '__version__') else 'unknown'}")
        except Exception as e:
            logger.warning(f"Could not get MCP SDK version: {e}")

        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if key.startswith("ODOO_") or key.startswith("MCP_"):
                if "PASSWORD" in key:
                    logger.info(f"  {key}: ***hidden***")
                else:
                    logger.info(f"  {key}: {value}")

        logger.info(f"MCP object type: {type(mcp)}")

        # Run appropriate server
        if TRANSPORT_MODE == "stdio":
            asyncio.run(run_stdio_server(logger))
        elif TRANSPORT_MODE == "sse":
            asyncio.run(run_sse_server(logger))

        logger.info("MCP server stopped normally")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
