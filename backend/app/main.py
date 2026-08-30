from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mcp.server import mcp, mcp_app
from app.routers import demo, feed, merchants, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Merchant Agent Platform",
    description="Backend API for merchant product feeds and test-mode Razorpay orders",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchants.router)
app.include_router(feed.router)
app.include_router(orders.router)

# Phase 3: REST bridge — browser demo calls the same MCP tool logic Claude uses
app.include_router(demo.router)

# Phase 2: MCP server (Streamable HTTP) mounted at /mcp
app.mount("/mcp", mcp_app)

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}