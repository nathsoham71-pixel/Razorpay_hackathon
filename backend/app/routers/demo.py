"""
Demo REST bridge — browser UI and MCP/Claude share identical business logic.

Routes here invoke the same MCP tool callables registered in Phase 2 (via
mcp._tool_manager), with merchant_id injected from the path instead of bearer auth.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update

from app.db.session import async_session_factory
from app.models.mandate import Mandate
from app.models.merchant import Merchant
from app.models.product import FeedStatus, Product, ProductFeedVersion
from app.routers.demo_bridge import call_mcp_tool
from app.services.mandate_engine import get_active_mandate

router = APIRouter(prefix="/demo", tags=["demo"])


class MandateUpsertBody(BaseModel):
    name: str = Field(default="default_upsell_mandate", min_length=1)
    max_upsell_amount_inr: Decimal = Field(..., ge=0)
    allowed_categories: list[str] = Field(default_factory=list)
    locked_fields: list[str] = Field(default_factory=list)


class SimulatePurchaseBody(BaseModel):
    items: list[dict[str, Any]] = Field(..., min_length=1)


class UpsellChatBody(BaseModel):
    buyer_message: str = Field(..., min_length=1)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)


class ConfirmPurchaseBody(BaseModel):
    razorpay_payment_id: str
    razorpay_signature: str


@router.get("/merchants/{merchant_id}/dashboard")
async def get_dashboard(merchant_id: UUID) -> dict[str, Any]:
    """Merchant info, latest feed summary, product counts, and active mandate."""
    async with async_session_factory() as db:
        merchant_result = await db.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        merchant = merchant_result.scalar_one_or_none()
        if merchant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

        feed_result = await db.execute(
            select(ProductFeedVersion)
            .where(
                ProductFeedVersion.merchant_id == merchant_id,
                ProductFeedVersion.status == FeedStatus.validated,
            )
            .order_by(ProductFeedVersion.version_number.desc())
            .limit(1)
        )
        latest_feed = feed_result.scalar_one_or_none()

        counts = await db.execute(
            select(
                func.count(Product.id),
                func.count(Product.id).filter(Product.is_agent_ready.is_(True)),
            ).where(Product.merchant_id == merchant_id)
        )
        total_products, agent_ready_count = counts.one()

        mandate = await get_active_mandate(db, merchant_id)

        return {
            "merchant": {
                "id": str(merchant.id),
                "business_name": merchant.business_name,
                "contact_email": merchant.contact_email,
                "mcp_access_token": merchant.mcp_access_token,
            },
            "latest_feed": (
                {
                    "id": str(latest_feed.id),
                    "version_number": latest_feed.version_number,
                    "status": latest_feed.status.value,
                    "uploaded_at": latest_feed.uploaded_at.isoformat(),
                    "product_count": len(
                        (latest_feed.acp_feed_json or {}).get("products", [])
                    ),
                }
                if latest_feed
                else None
            ),
            "product_count": int(total_products),
            "agent_ready_count": int(agent_ready_count),
            "active_mandate": (
                {
                    "id": str(mandate.id),
                    "name": mandate.name,
                    "max_upsell_amount_inr": float(mandate.max_upsell_amount_inr),
                    "allowed_categories": mandate.allowed_categories,
                    "locked_fields": mandate.locked_fields,
                    "is_active": mandate.is_active,
                }
                if mandate
                else None
            ),
        }


@router.post("/merchants/{merchant_id}/mandates", status_code=status.HTTP_201_CREATED)
async def upsert_mandate(merchant_id: UUID, body: MandateUpsertBody) -> dict[str, Any]:
    """Create or replace the active mandate for a merchant (one active at a time)."""
    async with async_session_factory() as db:
        merchant_result = await db.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        if merchant_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

        await db.execute(
            update(Mandate)
            .where(Mandate.merchant_id == merchant_id, Mandate.is_active.is_(True))
            .values(is_active=False)
        )

        mandate = Mandate(
            merchant_id=merchant_id,
            name=body.name,
            max_upsell_amount_inr=body.max_upsell_amount_inr,
            allowed_categories=body.allowed_categories,
            locked_fields=body.locked_fields,
            is_active=True,
        )
        db.add(mandate)
        await db.commit()
        await db.refresh(mandate)

        return {
            "id": str(mandate.id),
            "name": mandate.name,
            "max_upsell_amount_inr": float(mandate.max_upsell_amount_inr),
            "allowed_categories": mandate.allowed_categories,
            "locked_fields": mandate.locked_fields,
            "is_active": mandate.is_active,
        }


@router.post("/merchants/{merchant_id}/simulate/purchase")
async def simulate_purchase(merchant_id: UUID, body: SimulatePurchaseBody) -> dict[str, Any]:
    """Call initiate_purchase MCP tool with demo_browser_agent."""
    result = await call_mcp_tool(
        merchant_id,
        "initiate_purchase",
        {
            "buyer_agent_id": "demo_browser_agent",
            "items": body.items,
        },
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/orders/{order_id}/simulate/upsell-chat")
async def simulate_upsell_chat(order_id: UUID, body: UpsellChatBody) -> dict[str, Any]:
    """Call chat_with_merchant_agent MCP tool — same path Claude uses."""
    async with async_session_factory() as db:
        from app.models.order import Order

        order_result = await db.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        merchant_id = order.merchant_id

    result = await call_mcp_tool(
        merchant_id,
        "chat_with_merchant_agent",
        {
            "order_id": str(order_id),
            "buyer_message": body.buyer_message,
            "conversation_history": body.conversation_history,
        },
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/orders/{order_id}/confirm")
async def confirm_demo_purchase(order_id: UUID, body: ConfirmPurchaseBody) -> dict[str, Any]:
    """Call confirm_purchase MCP tool."""
    async with async_session_factory() as db:
        from app.models.order import Order

        order_result = await db.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        merchant_id = order.merchant_id

    result = await call_mcp_tool(
        merchant_id,
        "confirm_purchase",
        {
            "order_id": str(order_id),
            "razorpay_payment_id": body.razorpay_payment_id,
            "razorpay_signature": body.razorpay_signature,
        },
    )
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result
