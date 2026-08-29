from typing import Any

from mcp.server.mcpserver import MCPServer

from agent_agent_mcp.models.a2a import (
    A2ABody,
    A2AHeader,
    A2AAction,
    A2APayload,
    AgentRole,
)
from agent_agent_mcp.services.merchant_agent import (
    MerchantAgentCommunication,
    MerchantAgentError,
)
from agent_agent_mcp.services.session_manager import (
    SessionManager,
    SessionNotFoundError,
)


def register_tools(
    mcp: MCPServer,
    session_manager: SessionManager,
    merchant_agent: MerchantAgentCommunication,
) -> None:

    @mcp.tool()
    async def ask(
        session_id: str,
        agent_id: str,
        merchant_id: str,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Ask the Merchant Agent about products,
        availability, prices, or product details.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        try:
            session = await session_manager.get_or_create(
                session_id=session_id,
                agent_id=agent_id,
                merchant_id=merchant_id,
            )

        except PermissionError as exc:
            raise ValueError(
                "Session does not belong to this agent and merchant."
            ) from exc

        payload = A2APayload(
            header=A2AHeader(
                session_id=session.session_id,
                sender=AgentRole.CLAUDE_AGENT,
                action=A2AAction.QUERY,
            ),
            body=A2ABody(
                intent="product_query",
                parameters={
                    "query": query,
                    "filters": filters or {},
                },
                text_summary=query,
            ),
        )

        session.add_turn(payload)

        try:
            response = await merchant_agent.get_products(
                payload
            )

        except MerchantAgentError as exc:

            error_payload = A2APayload(
                header=A2AHeader(
                    session_id=session.session_id,
                    sender=AgentRole.MERCHANT_AGENT,
                    action=A2AAction.ERROR,
                ),
                body=A2ABody(
                    intent="merchant_agent_error",
                    parameters={},
                    text_summary=str(exc),
                ),
            )

            session.add_turn(error_payload)

            await session_manager.update(session)

            raise ValueError(
                "Merchant Agent could not process the request."
            ) from exc

        session.add_turn(response)

        await session_manager.update(session)

        return response.model_dump(mode="json")

    @mcp.tool()
    async def order(
        session_id: str,
        item_ids: list[str],
        quantities: list[int],
        payment_token: str | None = None,
        shipping_address: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Place an order through the Merchant Agent.
        """

        if not item_ids:
            raise ValueError(
                "At least one item is required."
            )

        if len(item_ids) != len(quantities):
            raise ValueError(
                "item_ids and quantities must have the same length."
            )

        if any(quantity <= 0 for quantity in quantities):
            raise ValueError(
                "All quantities must be greater than zero."
            )

        try:
            session = await session_manager.get(
                session_id
            )

        except SessionNotFoundError as exc:
            raise ValueError(
                "Session does not exist or has expired."
            ) from exc

        payload = A2APayload(
            header=A2AHeader(
                session_id=session.session_id,
                sender=AgentRole.CLAUDE_AGENT,
                action=A2AAction.ORDER_INTENT,
            ),
            body=A2ABody(
                intent="place_order",
                parameters={
                    "item_ids": item_ids,
                    "quantities": quantities,
                    "payment_token": payment_token,
                    "shipping_address": shipping_address or {},
                },
                text_summary=(
                    f"Place an order containing "
                    f"{len(item_ids)} item(s)."
                ),
            ),
        )

        session.add_turn(payload)

        try:
            response = await merchant_agent.place_order(
                payload
            )

        except MerchantAgentError as exc:

            error_payload = A2APayload(
                header=A2AHeader(
                    session_id=session.session_id,
                    sender=AgentRole.MERCHANT_AGENT,
                    action=A2AAction.ERROR,
                ),
                body=A2ABody(
                    intent="order_error",
                    parameters={},
                    text_summary=str(exc),
                ),
            )

            session.add_turn(error_payload)

            await session_manager.update(session)

            raise ValueError(
                "Merchant Agent could not process the order."
            ) from exc

        session.add_turn(response)

        session.active_order = response.body.parameters.get(
            "order"
        )

        await session_manager.update(session)

        return response.model_dump(mode="json")