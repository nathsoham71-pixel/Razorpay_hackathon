import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    url = "http://127.0.0.1:8000/mcp"

    async with streamable_http_client(url) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            print("\n=== CONNECTING TO MCP SERVER ===")

            await session.initialize()

            print("=== MCP SERVER INITIALIZED ===")

            result = await session.list_tools()

            print("\n=== AVAILABLE TOOLS ===")

            for tool in result.tools:
                print(f"\nName: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input schema: {tool.input_schema}")


if __name__ == "__main__":
    asyncio.run(main())