from decimal import Decimal
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.mcp.auth import resolve_merchant
from app.mcp.tools._helpers import error_response, require_merchant_id
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.services.mandate_engine import check_upsell_against_mandate
from app.services.merchant_agent import propose_upsell
from app.services.razorpay_client import RazorpayIntegrationError, create_test_order


def register_upsell_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="chat_with_merchant_agent",
        description=(
            "Chat with the GPT-powered merchant agent about upsell suggestions during checkout. "
            "GPT proposes upsells; a deterministic mandate engine approves or rejects before "
            "any item is added to the order. Returns upsell_status: none_proposed | approved | rejected."
        ),
    )
    async def chat_with_merchant_agent(
        order_id: str,
        buyer_message: str,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Upsell chat flow: GPT proposes -> mandate_engine enforces -> order updated only if approved.
        """
        merchant_ref = require_merchant_id()
        if isinstance(merchant_ref, dict):
            return merchant_ref

        history = conversation_history or []

        try:
            async with async_session_factory() as db:
                order_uuid = UUID(order_id)
                result = await db.execute(
                    select(Order)
                    .options(selectinload(Order.items).selectinload(OrderItem.product))
                    .where(Order.id == order_uuid, Order.merchant_id == merchant_ref)
                )
                order = result.scalar_one_or_none()
                if order is None:
                    return error_response("Order not found")
                if order.status != OrderStatus.created:
                    return error_response("Order must be in created status for upsell chat")

                cart_categories = {item.product.category for item in order.items if item.product}
                cart_product_ids = {str(item.product_id) for item in order.items}

                upsell_query = select(Product).where(
                    Product.merchant_id == merchant_ref,
                    Product.is_agent_ready.is_(True),
                )
                if cart_categories:
                    category_filters = [
                        Product.category.ilike(cat) for cat in cart_categories
                    ]
                    upsell_query = upsell_query.where(or_(*category_filters))

                upsell_result = await db.execute(upsell_query.limit(20))
                candidates = upsell_result.scalars().all()
                available_upsell_products = [
                    {
                        "product_id": str(p.id),
                        "sku": p.sku,
                        "title": p.title,
                        "category": p.category,
                        "price_inr": float(p.price_inr),
                        "stock_quantity": p.stock_quantity,
                    }
                    for p in candidates
                    if str(p.id) not in cart_product_ids and p.stock_quantity > 0
                ]

                cart_context = {
                    "order_id": str(order.id),
                    "items": [
                        {
                            "product_id": str(item.product_id),
                            "title": item.product.title if item.product else None,
                            "quantity": item.quantity,
                            "unit_price_inr": float(item.unit_price_inr),
                        }
                        for item in order.items
                    ],
                    "total_inr": float(order.total_amount_inr),
                    "categories": list(cart_categories),
                }

                full_history = [
                    *history,
                    {"role": "user", "content": buyer_message},
                ]
                proposal = await propose_upsell(
                    conversation_history=full_history,
                    cart_context=cart_context,
                    available_upsell_products=available_upsell_products,
                )

                reply_text = proposal.get("reply_text", "")
                proposed = proposal.get("proposed_upsell")
                requested_field_changes = proposal.get("requested_field_changes") or []

                if proposed is None:
                    return {
                        "reply_text": reply_text,
                        "upsell_status": "none_proposed",
                    }

                proposed_category = str(proposed.get("category", ""))
                proposed_price = Decimal(str(proposed.get("price_inr", 0)))

                mandate_result = await check_upsell_against_mandate(
                    db=db,
                    merchant_id=merchant_ref,
                    proposed_item_category=proposed_category,
                    proposed_item_price_inr=proposed_price,
                    requested_field_changes=requested_field_changes,
                )

                if not mandate_result.approved:
                    limit_note = ""
                    if mandate_result.max_allowed_inr is not None:
                        limit_note = (
                            f" [System: upsell blocked — exceeds mandate limit of "
                            f"₹{mandate_result.max_allowed_inr}]"
                        )
                    elif mandate_result.reason == "no_active_mandate":
                        limit_note = " [System: upsell blocked — no active mandate configured]"
                    elif mandate_result.reason == "category_not_allowed":
                        limit_note = " [System: upsell blocked — category not allowed by mandate]"
                    elif mandate_result.reason == "locked_field_violation":
                        limit_note = " [System: upsell blocked — locked field change requested]"

                    return {
                        "reply_text": f"{reply_text}{limit_note}",
                        "upsell_status": "rejected",
                        "rejection_reason": mandate_result.reason,
                        "max_allowed_inr": (
                            float(mandate_result.max_allowed_inr)
                            if mandate_result.max_allowed_inr is not None
                            else None
                        ),
                    }

                product_id = UUID(str(proposed["product_id"]))
                product_result = await db.execute(
                    select(Product).where(
                        Product.id == product_id,
                        Product.merchant_id == merchant_ref,
                    )
                )
                product = product_result.scalar_one_or_none()
                if product is None:
                    return error_response("Proposed upsell product not found")
                if product.stock_quantity < 1:
                    return error_response("Proposed upsell product out of stock")

                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=1,
                        unit_price_inr=product.price_inr,
                    )
                )
                order.total_amount_inr += product.price_inr

                merchant = await resolve_merchant(db, merchant_ref)
                if merchant is None:
                    return error_response("Merchant not found")

                try:
                    razorpay_order = create_test_order(
                        amount_inr=float(order.total_amount_inr),
                        receipt_id=str(order.id),
                        merchant=merchant,
                    )
                    order.razorpay_order_id = razorpay_order["id"]
                except RazorpayIntegrationError as exc:
                    await db.rollback()
                    return error_response(str(exc))

                await db.commit()

                return {
                    "reply_text": reply_text,
                    "upsell_status": "approved",
                    "new_item": {
                        "product_id": str(product.id),
                        "sku": product.sku,
                        "title": product.title,
                        "quantity": 1,
                        "unit_price_inr": float(product.price_inr),
                    },
                    "new_total_inr": float(order.total_amount_inr),
                    "razorpay_order_id": order.razorpay_order_id,
                }
        except Exception as exc:
            return error_response(f"chat_with_merchant_agent failed: {exc}")
