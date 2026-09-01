# Merchant Agent Platform

An **agent-commerce platform** that lets AI buyer agents (Claude, Cursor, or any MCP client) browse merchant catalogs, place Razorpay test-mode orders, chat with a GPT-powered upsell agent, and complete purchases — all through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

Merchants upload a CSV product feed, configure spending mandates, and expose their catalog to external agents via a secured MCP endpoint.

## Features

- **CSV product feed ingestion** — upload merchant catalogs and translate them into agent-ready product data (ACP/AP2 JSON)
- **MCP server** — five tools for catalog search, purchase initiation, payment confirmation, and upsell chat
- **Razorpay test-mode payments** — create orders and verify payment signatures (no real money)
- **Merchant upsell agent** — OpenAI GPT proposes upsells; a deterministic mandate engine approves or rejects them
- **Spending mandates** — cap upsell amounts, restrict categories, and lock fields
- **React demo UI** — dashboard, mandate config, and buyer-agent simulator with Razorpay Checkout.js
- **REST demo bridge** — browser UI calls the same MCP tool logic that Claude uses

## Architecture

```mermaid
flowchart TB
    subgraph clients [Buyer Agents]
        Claude[Claude Desktop / Cursor MCP]
        Simulator[React Simulator]
    end

    subgraph backend [FastAPI Backend :8000]
        REST[REST API]
        Demo["/demo bridge"]
        MCP["/mcp MCP Server"]
        Services[Services]
    end

    subgraph external [External APIs]
        OpenAI[OpenAI GPT]
        Razorpay[Razorpay Test API]
    end

    DB[(PostgreSQL)]

    Claude -->|Bearer token| MCP
    Simulator --> Demo
    Demo --> MCP
    REST --> Services
    MCP --> Services
    Services --> DB
    Services --> OpenAI
    Services --> Razorpay
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy (async), Alembic, asyncpg |
| MCP | `mcp` SDK 1.x (FastMCP, Streamable HTTP) |
| Payments | Razorpay test mode |
| AI upsell | OpenAI API (`gpt-4o-mini` by default) |
| Frontend | React 18, Vite, Tailwind CSS 4 |
| Database | PostgreSQL 16 |
| Deployment | Docker, Render (`render.yaml`) |

## Project Structure

```text
razor_pay/
├── backend/
│   ├── app/
│   │   ├── mcp/              # MCP server + tools
│   │   ├── routers/          # REST + /demo bridge
│   │   ├── services/         # Razorpay, feed translator, mandate engine, GPT agent
│   │   └── models/           # Merchant, Product, Order, Mandate
│   ├── scripts/              # MCP purchase helper scripts
│   ├── alembic/              # Database migrations
│   ├── sample_feed.csv       # Example product feed
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── pages/            # Dashboard, Mandate, Simulator
│       └── components/
├── docker-compose.yml
├── render.yaml               # Render Blueprint (backend + Postgres)
├── RUNBOOK.md                # Detailed local setup
└── DEPLOY.md                 # Production deployment guide
```

## Prerequisites

- **Docker Desktop** (for PostgreSQL)
- **Python 3.11**
- **Node.js 18+** (for frontend)
- **Razorpay test keys** — [dashboard.razorpay.com](https://dashboard.razorpay.com)
- **OpenAI API key** (for upsell chat)

## Quick Start (Local)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your Razorpay test keys and OpenAI API key
```

### 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Start the frontend (optional)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### 5. Create a merchant and upload products

**PowerShell:**

```powershell
$body = @{ business_name = "Demo Store"; contact_email = "demo@example.com" } | ConvertTo-Json
$merchant = Invoke-RestMethod -Uri "http://localhost:8000/merchants" -Method POST -ContentType "application/json" -Body $body
$merchant.id          # save as MERCHANT_ID
$merchant.mcp_access_token  # save for MCP config
```

```powershell
curl.exe -X POST "http://localhost:8000/merchants/$($merchant.id)/feed/upload" -F "file=@backend/sample_feed.csv"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Async Postgres URL (`postgresql+asyncpg://...`) |
| `RAZORPAY_KEY_ID` | Yes | Global Razorpay test key ID |
| `RAZORPAY_KEY_SECRET` | Yes | Global Razorpay test secret |
| `OPENAI_API_KEY` | Yes | For upsell chat MCP tool |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `PUBLIC_BASE_URL` | Prod | Public API URL, e.g. `https://merchant-platform-api.onrender.com` |
| `CORS_ORIGINS` | No | Comma-separated frontend URLs (default: `http://localhost:5173`) |
| `UPLOAD_DIR` | No | CSV upload directory (default: `/tmp/feed_uploads`) |
| `VITE_API_BASE_URL` | Frontend | Backend URL (default: `http://localhost:8000`) |

On Render, `RENDER_EXTERNAL_URL` is auto-detected if `PUBLIC_BASE_URL` is not set.

## MCP Integration

The MCP server runs inside the FastAPI backend at `/mcp` (not a separate process). Each merchant gets a unique `mcp_access_token` on creation.

### MCP Tools

| Tool | Description |
|------|-------------|
| `get_product_feed` | Latest validated ACP/AP2 feed JSON |
| `search_products` | Search agent-ready products by title/description |
| `initiate_purchase` | Create order + Razorpay test checkout details |
| `confirm_purchase` | Verify Razorpay payment signature and mark order paid |
| `chat_with_merchant_agent` | GPT upsell chat with mandate enforcement |

Merchant scope is determined by the Bearer token — agents must not pass `merchant_id`.

### Connect Cursor

Add to `~/.cursor/mcp.json` (Windows: `%USERPROFILE%\.cursor\mcp.json`):

```json
{
  "mcpServers": {
    "merchant-platform": {
      "url": "https://merchant-platform-api.onrender.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_ACCESS_TOKEN"
      }
    }
  }
}
```

Restart Cursor. The `mcpServers` wrapper is required — do not put `url` at the root level.

### Connect Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` with the same structure, then restart Claude Desktop.

### Test MCP from the command line

```bash
cd backend
python scripts/complete_purchase_mcp.py "wireless mouse"
```

This runs the full flow: `search_products` → `initiate_purchase` → `confirm_purchase`.

## Frontend Pages

| Route | Purpose |
|-------|---------|
| `/` | Upload CSV feeds, view translation stats |
| `/mandate` | Configure agent spending mandates (max amount, categories) |
| `/simulator` | Simulate buyer-agent purchases with Razorpay test checkout |

Razorpay test card: `4111 1111 1111 1111`, any future expiry, any CVV.

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/merchants` | POST | Create merchant (+ MCP token) |
| `/merchants/{id}/feed/upload` | POST | Upload CSV product feed |
| `/merchants/{id}/products` | GET | List products |
| `/orders` | POST | Create Razorpay test order |
| `/orders/{id}/verify` | POST | Verify payment signature |
| `/demo/*` | Various | Browser bridge (same logic as MCP tools) |
| `/mcp` | MCP | Streamable HTTP MCP endpoint |
| `/docs` | GET | Swagger UI |

## Deployment

For public hosting (so Claude or Cursor can reach MCP from outside your machine), see **[DEPLOY.md](./DEPLOY.md)**.

Quick summary:

1. Push to GitHub
2. Deploy via Render Blueprint (`render.yaml`)
3. Set env vars: `PUBLIC_BASE_URL`, `RAZORPAY_*`, `OPENAI_API_KEY`
4. Create merchant, upload feed, configure MCP client

Live demo API: `https://merchant-platform-api.onrender.com`

## Docker (full stack)

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
```

Backend: [http://localhost:8000](http://localhost:8000)

## Running Tests

```bash
cd backend
pytest
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| MCP returns `421 Invalid Host header` | Ensure latest code is deployed; MCP DNS rebinding is disabled behind Render proxy |
| MCP tools not showing in Cursor | Use `mcpServers` wrapper in config; restart Cursor |
| `curl -d "{\"...\"}"` fails in PowerShell | Use `Invoke-RestMethod` or `curl.exe` with a file body |
| CORS errors from frontend | Add frontend URL to `CORS_ORIGINS` |
| Upsell chat fails | Set `OPENAI_API_KEY` |
| Render cold start (~30s) | Free tier sleeps after inactivity; retry the request |
| `mcp` import error on deploy | Pinned to `mcp>=1.27.0,<2` (v2 renamed `FastMCP`) |

## License

This project was built for the Razorpay hackathon demo. Use and modify as needed.

## Related Docs

- [RUNBOOK.md](./RUNBOOK.md) — step-by-step local development
- [DEPLOY.md](./DEPLOY.md) — production deployment on Render
