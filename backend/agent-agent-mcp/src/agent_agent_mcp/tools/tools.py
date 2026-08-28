from typing import Any

from mcp.server.mcpserver import MCPServer

from agent_agent_mcp.services.agent_communication import AgentCommunication


def register_tools(mcp: MCPServer):
    """
    Register all public MCP tools.

    These are the capabilities visible to external agents.
    """

    communication = AgentCommunication()

    @mcp.tool()
    def get_products(request: dict[str, Any]) -> dict[str, Any]:
        """
        Get products and product details from the Merchant Agent.

        The request structure is intentionally flexible for now
        and will be finalized later.
        """

        return communication.get_products(request)

    @mcp.tool()
    def place_order(request: dict[str, Any]) -> dict[str, Any]:
        """
        Send an order request to the Merchant Agent.

        The request structure is intentionally flexible for now
        and will be finalized later.
        """

        return communication.place_order(request)