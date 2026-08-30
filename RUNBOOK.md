# RUNBOOK — Merchant Agent Platform (Phase 1)

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Python 3.11
- Project root `.env` configured (copy from `.env.example`)

Ensure `DATABASE_URL` uses the async driver:

```text
DATABASE_URL=postgresql+asyncpg://postgres:devpass@localhost:5432/razorpay_merchant_website
```

## 1. Start PostgreSQL

From the project root:

```bash
docker compose up -d postgres
```

Wait until the healthcheck passes:

```bash
docker compose ps
```

## 2. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 3. Run database migrations

```bash
cd backend
alembic upgrade head
```

## 4. Start the API server

```bash
cd backend
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## 5. Sample API calls

### Create a merchant

```bash
curl -X POST http://localhost:8000/merchants \
  -H "Content-Type: application/json" \
  -d "{\"business_name\":\"Demo Store\",\"contact_email\":\"demo@example.com\"}"
```

Save the returned `id` as `MERCHANT_ID`.

### Upload a CSV product feed

Create a sample CSV (`sample_feed.csv`):

```csv
Product Name,Selling Price,SKU,Qty,Category
Wireless Mouse,499,WM-001,50,electronics
USB-C Cable,,CB-002,100,accessories
```

```bash
curl -X POST "http://localhost:8000/merchants/{MERCHANT_ID}/feed/upload" \
  -F "file=@sample_feed.csv"
```

### List agent-ready products

```bash
curl "http://localhost:8000/merchants/{MERCHANT_ID}/products?is_agent_ready=true"
```

Save a product `id` as `PRODUCT_ID`.

### Create a Razorpay test order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d "{\"merchant_id\":\"{MERCHANT_ID}\",\"buyer_agent_id\":\"demo_agent\",\"items\":[{\"product_id\":\"{PRODUCT_ID}\",\"quantity\":1}]}"
```

Use the returned `razorpay_order.id` and complete payment in Razorpay test checkout, then verify:

```bash
curl -X POST "http://localhost:8000/orders/{ORDER_ID}/verify" \
  -H "Content-Type: application/json" \
  -d "{\"razorpay_payment_id\":\"pay_xxx\",\"razorpay_signature\":\"signature_xxx\"}"
```

## Optional: run full stack via Docker Compose

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
```

The backend service mounts `./backend` for hot reload during development.
