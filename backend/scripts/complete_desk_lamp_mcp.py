"""Full desk-lamp purchase via merchant MCP: search -> initiate -> confirm."""
import asyncio
import hashlib
import hmac
import json
import os
import uuid
from pathlib import Path

import httpx
from dotenv import dotenv_values
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def load_mcp_config() -> tuple[str, str]:
    mcp_json = Path.home() / ".cursor" / "mcp.json"
    cfg = json.loads(mcp_json.read_text(encoding="utf-8"))
    server = cfg["mcpServers"]["merchant-platform"]
    url = server["url"]
    token = server["headers"]["Authorization"].removeprefix("Bearer ").strip()
    return url, token


def load_razorpay_secret() -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    values = dotenv_values(env_path)
    secret = values.get("RAZORPAY_KEY_SECRET", "")
    if not secret:
        raise SystemExit("RAZORPAY_KEY_SECRET missing in project .env")
    return secret


def make_test_signature(razorpay_order_id: str, payment_id: str, secret: str) -> str:
    message = f"{razorpay_order_id}|{payment_id}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


async def main() -> None:
    url, token = load_mcp_config()
    # No trailing slash — avoids 421 Misdirected Request on Render
    url = url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Connecting to MCP at {url} ...")
    async with httpx.AsyncClient(
        headers=headers,
        timeout=120.0,
        follow_redirects=True,
        http2=False,
    ) as http_client:
        async with streamable_http_client(url, http_client=http_client) as (
            read_stream,
            write_stream,
            _get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("MCP session initialized.\n")

                print("=== 1. search_products: desk lamp ===")
                search_result = await session.call_tool(
                    "search_products", {"query": "desk lamp"}
                )
                products = json.loads(search_result.content[0].text)
                if isinstance(products, dict) and "error" in products:
                    raise SystemExit(f"search_products failed: {products['error']}")
                if not products:
                    raise SystemExit("No desk lamp products found")

                lamp = products[0]
                print(json.dumps(lamp, indent=2))

                print("\n=== 2. initiate_purchase ===")
                purchase_result = await session.call_tool(
                    "initiate_purchase",
                    {
                        "buyer_agent_id": "cursor_agent",
                        "items": [{"product_id": lamp["id"], "quantity": 1}],
                    },
                )
                order = json.loads(purchase_result.content[0].text)
                if "error" in order:
                    raise SystemExit(f"initiate_purchase failed: {order['error']}")
                print(json.dumps(order, indent=2))

                razorpay_order_id = order["razorpay_order_id"]
                internal_order_id = order["order_id"]
                payment_id = f"pay_{uuid.uuid4().hex[:14]}"
                signature = make_test_signature(
                    razorpay_order_id, payment_id, load_razorpay_secret()
                )

                print("\n=== 3. confirm_purchase ===")
                confirm_result = await session.call_tool(
                    "confirm_purchase",
                    {
                        "order_id": internal_order_id,
                        "razorpay_payment_id": payment_id,
                        "razorpay_signature": signature,
                    },
                )
                confirmed = json.loads(confirm_result.content[0].text)
                print(json.dumps(confirmed, indent=2))

                if confirmed.get("status") == "paid":
                    print(
                        f"\nDone. Desk Lamp purchased for INR {confirmed.get('total_amount_inr', lamp.get('price_inr'))}."
                    )
                else:
                    raise SystemExit(f"Payment not confirmed: {confirmed}")


if __name__ == "__main__":
    asyncio.run(main())
