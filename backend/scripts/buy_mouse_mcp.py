"""Connect to merchant MCP and buy a mouse via search + initiate_purchase."""
import asyncio
import json
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def load_mcp_config() -> tuple[str, str]:
    mcp_json = Path.home() / ".cursor" / "mcp.json"
    cfg = json.loads(mcp_json.read_text(encoding="utf-8"))
    server = cfg["mcpServers"]["merchant-platform"]
    url = server["url"]
    token = server["headers"]["Authorization"].removeprefix("Bearer ").strip()
    return url, token


async def main() -> None:
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

                tools = await session.list_tools()
                print("Available tools:", [t.name for t in tools.tools])

                print("\n=== Searching for mouse ===")
                search_result = await session.call_tool("search_products", {"query": "mouse"})
                products = json.loads(search_result.content[0].text)
                if isinstance(products, dict) and "error" in products:
                    raise SystemExit(f"search_products failed: {products['error']}")
                if not products:
                    raise SystemExit("No mouse products found")

                mouse = products[0]
                print(json.dumps(mouse, indent=2))

                print("\n=== Initiating purchase ===")
                purchase_result = await session.call_tool(
                    "initiate_purchase",
                    {
                        "buyer_agent_id": "cursor_agent",
                        "items": [{"product_id": mouse["id"], "quantity": 1}],
                    },
                )
                order = json.loads(purchase_result.content[0].text)
                if "error" in order:
                    raise SystemExit(f"initiate_purchase failed: {order['error']}")

                print(json.dumps(order, indent=2))
                print("\nPurchase initiated successfully.")


if __name__ == "__main__":
    asyncio.run(main())
