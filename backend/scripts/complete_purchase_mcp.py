"""Full product purchase via merchant MCP: search -> initiate -> confirm."""
import asyncio
import hashlib
import hmac
import json
import sys
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
    secret = dotenv_values(env_path).get("RAZORPAY_KEY_SECRET", "")
    if not secret:
        raise SystemExit("RAZORPAY_KEY_SECRET missing in project .env")
    return secret


def parse_tool_payload(result) -> dict | list:
    data = json.loads(result.content[0].text)
    if isinstance(data, dict) and "error" in data:
        raise SystemExit(data["error"])
    return data


async def buy_product(query: str) -> None:
    url, token = load_mcp_config()
    if not url.endswith("/"):
        url += "/"
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

                print(f"=== 1. search_products: {query} ===")
                products = parse_tool_payload(
                    await session.call_tool("search_products", {"query": query})
                )
                if isinstance(products, dict):
                    products = [products]
                if not products:
                    raise SystemExit(f"No products found for '{query}'")

                product = products[0]
                print(json.dumps(product, indent=2))

                print("\n=== 2. initiate_purchase ===")
                order = parse_tool_payload(
                    await session.call_tool(
                        "initiate_purchase",
                        {
                            "buyer_agent_id": "cursor_agent",
                            "items": [{"product_id": product["id"], "quantity": 1}],
                        },
                    )
                )
                if not isinstance(order, dict):
                    raise SystemExit(f"Unexpected order response: {order}")
                print(json.dumps(order, indent=2))

                payment_id = f"pay_{uuid.uuid4().hex[:14]}"
                message = f"{order['razorpay_order_id']}|{payment_id}".encode()
                signature = hmac.new(
                    load_razorpay_secret().encode(), message, hashlib.sha256
                ).hexdigest()

                print("\n=== 3. confirm_purchase ===")
                confirmed = parse_tool_payload(
                    await session.call_tool(
                        "confirm_purchase",
                        {
                            "order_id": order["order_id"],
                            "razorpay_payment_id": payment_id,
                            "razorpay_signature": signature,
                        },
                    )
                )
                if not isinstance(confirmed, dict):
                    raise SystemExit(f"Unexpected confirm response: {confirmed}")
                print(json.dumps(confirmed, indent=2))

                if confirmed.get("status") == "paid":
                    print(
                        f"\nDone. {product['title']} purchased for INR "
                        f"{confirmed.get('total_amount_inr', product.get('price_inr'))}."
                    )
                else:
                    raise SystemExit(f"Payment not confirmed: {confirmed}")


if __name__ == "__main__":
    product_query = sys.argv[1] if len(sys.argv) > 1 else "desk lamp"
    asyncio.run(buy_product(product_query))
