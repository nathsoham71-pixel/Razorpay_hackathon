from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server.mcpserver import MCPServer

from agent_agent_mcp.services.session_manager import SessionManager
from agent_agent_mcp.services.merchant_agent import (
    MerchantAgentCommunication,
)
from agent_agent_mcp.tools.tools import register_tools


# ---------------------------------------------------------
# Application services
# ---------------------------------------------------------

session_manager = SessionManager(
    ttl_seconds=1800,
    cleanup_interval_seconds=300,
)

merchant_agent = MerchantAgentCommunication()


# ---------------------------------------------------------
# MCP Server
# ---------------------------------------------------------

mcp = MCPServer(
    "Merchant Agent MCP"
)


register_tools(
    mcp=mcp,
    session_manager=session_manager,
    merchant_agent=merchant_agent,
)


# IMPORTANT:
# Because we mount this app at /mcp below, "/" here means
# the MCP endpoint will be exactly /mcp.
mcp_app = mcp.streamable_http_app(
    json_response=True,
    streamable_http_path="/",
)


# ---------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    await session_manager.start()

    # MCP's own session manager must also be started
    async with mcp.session_manager.run():
        yield

    await session_manager.stop()


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Merchant Agent MCP Server",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "merchant-agent-mcp",
    }


# MCP endpoint
app.mount(
    "/mcp",
    mcp_app,
)