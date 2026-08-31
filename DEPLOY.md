# Deploy — Option B (Public hosting for Claude MCP)

Host the **backend + Postgres** publicly so Claude (Desktop, mobile, or cloud) can reach your MCP tools at `https://your-api.com/mcp`.

The React website is **optional** — only needed if you want a browser dashboard. Claude connects directly to `/mcp`.

---

## What gets deployed

| Component | Required | Where |
|-----------|----------|-------|
| Backend API + MCP (`/mcp`) | Yes | Render (Docker) |
| PostgreSQL | Yes | Render managed DB |
| React frontend | Optional | Vercel / Netlify |

---

## Step 1 — Push code to GitHub

Render deploys from a Git repo. If you don't have a remote yet:

```bash
git add .
git commit -m "Add production deployment config"
# Create a repo on GitHub, then:
git remote add origin https://github.com/YOUR_USER/razor_pay.git
git push -u origin main
```

---

## Step 2 — Deploy backend on Render

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **New → Blueprint** → connect your repo.
3. Render reads `render.yaml` and creates:
   - `merchant-platform-db` (Postgres)
   - `merchant-platform-api` (Docker web service)
4. When prompted, set these **secret env vars** in the Render dashboard:

   | Variable | Example |
   |----------|---------|
   | `PUBLIC_BASE_URL` | `https://merchant-platform-api.onrender.com` |
   | `RAZORPAY_KEY_ID` | `rzp_test_...` |
   | `RAZORPAY_KEY_SECRET` | your test secret |
   | `OPENAI_API_KEY` | `sk-...` |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app` (or leave localhost if no frontend) |

5. Wait for deploy to finish. Migrations run automatically on startup.
6. Verify: `curl https://YOUR-SERVICE.onrender.com/health` → `{"status":"ok"}`

> **Note:** Free Render services spin down after inactivity. First request may take ~30s to wake up.

---

## Step 3 — Create merchant + get MCP token

```bash
curl -X POST https://YOUR-SERVICE.onrender.com/merchants \
  -H "Content-Type: application/json" \
  -d '{"business_name":"Demo Store","contact_email":"demo@example.com"}'
```

Save `id` and `mcp_access_token` from the response.

Upload a product feed:

```bash
curl -X POST "https://YOUR-SERVICE.onrender.com/merchants/MERCHANT_ID/feed/upload" \
  -F "file=@backend/sample_feed.csv"
```

---

## Step 4 — Connect Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "merchant-platform": {
      "url": "https://YOUR-SERVICE.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_ACCESS_TOKEN"
      }
    }
  }
}
```

Restart Claude Desktop. You should see 5 tools: `get_product_feed`, `search_products`, `initiate_purchase`, `confirm_purchase`, `chat_with_merchant_agent`.

---

## Step 5 (Optional) — Deploy frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → Import Git repo.
2. Set **Root Directory** to `frontend`.
3. Add env var: `VITE_API_BASE_URL=https://YOUR-SERVICE.onrender.com`
4. Deploy.
5. Add the Vercel URL to backend `CORS_ORIGINS` on Render (comma-separated).

---

## Claude connection checklist

- [ ] Backend health check returns OK over HTTPS
- [ ] `PUBLIC_BASE_URL` matches your actual Render URL
- [ ] Merchant created, `mcp_access_token` saved
- [ ] CSV feed uploaded (products exist)
- [ ] Claude config uses `https://.../mcp` + Bearer token
- [ ] Claude restarted after config change

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| MCP tools not showing in Claude | Check Bearer token; restart Claude |
| CORS errors from frontend | Add frontend URL to `CORS_ORIGINS` on Render |
| 502 on first request | Free tier cold start — wait and retry |
| DB connection failed | Confirm `DATABASE_URL` is linked to Postgres in Render |
| Upsell chat fails | Set `OPENAI_API_KEY` on Render |

---

## Alternative platforms

The same Docker image (`backend/Dockerfile`) works on **Railway**, **Fly.io**, or **AWS ECS**. Set the same env vars and expose port `8000` (or `$PORT`).
