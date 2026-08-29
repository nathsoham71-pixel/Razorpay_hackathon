from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from agent_agent_mcp.models.a2a import A2APayload


logger = logging.getLogger(__name__)


class MerchantAgentError(Exception):
    pass


class MerchantAgentCommunication:
    """
    Handles A2A-style communication between the MCP server
    and the Merchant Agent.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float = 20.0,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "MERCHANT_AGENT_URL",
                "http://127.0.0.1:9000",
            )
        ).rstrip("/")

        self.timeout = httpx.Timeout(timeout_seconds)

    async def get_products(
        self,
        payload: A2APayload,
    ) -> A2APayload:

        return await self._send(payload)

    async def place_order(
        self,
        payload: A2APayload,
    ) -> A2APayload:

        return await self._send(payload)

    async def _send(
        self,
        payload: A2APayload,
    ) -> A2APayload:

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    f"{self.base_url}/a2a",
                    json=payload.model_dump(mode="json"),
                )

                response.raise_for_status()

                return A2APayload.model_validate(
                    response.json()
                )

        except httpx.HTTPStatusError as exc:

            logger.error(
                "Merchant Agent returned HTTP %s",
                exc.response.status_code,
            )

            raise MerchantAgentError(
                "Merchant Agent rejected the request."
            ) from exc

        except httpx.RequestError as exc:

            logger.error(
                "Merchant Agent communication failed: %s",
                exc,
            )

            raise MerchantAgentError(
                "Merchant Agent is currently unavailable."
            ) from exc

        except ValueError as exc:

            logger.error(
                "Invalid A2A response from Merchant Agent"
            )

            raise MerchantAgentError(
                "Merchant Agent returned an invalid response."
            ) from exc