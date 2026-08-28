from mcp.server.mcpserver import MCPServer

from agent_agent_mcp.tools.tools import register_tools


mcp = MCPServer(
    "Merchant MCP"
)

register_tools(mcp)


def main():
    """Start the Merchant MCP server."""
    mcp.run(
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()