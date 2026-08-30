import secrets
from uuid import UUID

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.merchant import Merchant


class MerchantTokenVerifier:
    """Verify bearer tokens against Merchant.mcp_access_token."""

    async def verify_token(self, token: str) -> AccessToken | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Merchant).where(Merchant.mcp_access_token == token)
            )
            merchant = result.scalar_one_or_none()
            if merchant is None:
                return None
            return AccessToken(
                token=token,
                client_id=str(merchant.id),
                scopes=["mcp"],
                claims={"merchant_id": str(merchant.id)},
            )


def generate_mcp_access_token() -> str:
    return secrets.token_urlsafe(32)


def get_authenticated_merchant_id() -> UUID | None:
    """Resolve merchant_id from MCP bearer auth context."""
    access = get_access_token()
    if access is None or not access.claims:
        return None
    merchant_id = access.claims.get("merchant_id")
    if merchant_id is None:
        return None
    return UUID(str(merchant_id))


async def resolve_merchant(db_session, merchant_id: UUID) -> Merchant | None:
    result = await db_session.execute(
        select(Merchant).where(Merchant.id == merchant_id)
    )
    return result.scalar_one_or_none()
