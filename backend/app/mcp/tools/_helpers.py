from typing import Any
from uuid import UUID

from app.mcp.auth import get_authenticated_merchant_id


def require_merchant_id() -> UUID | dict[str, Any]:
    merchant_id = get_authenticated_merchant_id()
    if merchant_id is None:
        return {"error": "Unauthorized — valid Bearer token required"}
    return merchant_id


def error_response(message: str) -> dict[str, Any]:
    return {"error": message}
