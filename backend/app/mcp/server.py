"""
MCP server for Merchant Agent Platform (Phase 2).

Transport: Streamable HTTP (mcp.server.fastmcp.FastMCP.streamable_http_app).
Mounted on the main FastAPI app at /mcp — not a separate process.

SDK note (mcp==1.x): uses FastMCP with streamable-http transport, which supersedes
the legacy SSE-only pattern. Clients connect to http://localhost:8000/mcp with
Authorization: Bearer <merchant mcp_access_token>.
"""

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.config import get_settings
from app.mcp.auth import MerchantTokenVerifier
from app.mcp.tools.catalog_tools import register_catalog_tools
from app.mcp.tools.purchase_tools import register_purchase_tools
from app.mcp.tools.upsell_tools import register_upsell_tools

_settings = get_settings()
_mcp_url = _settings.mcp_resource_url
_transport_security = TransportSecuritySettings(
    # Behind Render's reverse proxy; bearer auth protects the endpoint.
    enable_dns_rebinding_protection=False,
)

# Bearer auth via MerchantTokenVerifier; streamable-http at mount path /
mcp = FastMCP(
    "Merchant Agent Platform MCP",
    instructions=(
        "Tools for browsing merchant catalogs, initiating test purchases, "
        "chatting with the merchant upsell agent, and confirming Razorpay payments. "
        "Merchant scope is determined by the Bearer token — do not pass merchant_id."
    ),
    token_verifier=MerchantTokenVerifier(),
    auth=AuthSettings(
        issuer_url=_mcp_url,
        resource_server_url=_mcp_url,
    ),
    host="0.0.0.0",
    transport_security=_transport_security,
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
)

register_catalog_tools(mcp)
register_purchase_tools(mcp)
register_upsell_tools(mcp)

# Mounted at /mcp in main.py, so internal path is /
mcp_app = mcp.streamable_http_app()
