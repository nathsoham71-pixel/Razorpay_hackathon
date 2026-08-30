"""Helper to invoke MCP tool functions with an explicit merchant_id (demo bridge only)."""

from contextlib import contextmanager
from typing import Any
from unittest.mock import patch
from uuid import UUID

from app.mcp.server import mcp


@contextmanager
def _merchant_tool_context(merchant_id: UUID):
    def _require() -> UUID:
        return merchant_id

    patches = [
        patch("app.mcp.tools.purchase_tools.require_merchant_id", _require),
        patch("app.mcp.tools.upsell_tools.require_merchant_id", _require),
        patch("app.mcp.tools.catalog_tools.require_merchant_id", _require),
    ]
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in reversed(patches):
            p.stop()


async def call_mcp_tool(merchant_id: UUID, tool_name: str, arguments: dict[str, Any]) -> Any:
    """Run a registered MCP tool as if authenticated for merchant_id."""
    with _merchant_tool_context(merchant_id):
        return await mcp._tool_manager.call_tool(tool_name, arguments)
