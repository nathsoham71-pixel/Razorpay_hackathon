from decimal import Decimal
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.mcp.auth import resolve_merchant
from app.mcp.tools._helpers import error_response, require_merchant_id
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.services.razorpay_client import (
    RazorpayIntegrationError,
    create_test_order,
    verify_payment_signature,
)


def register_purchase_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="initiate_purchase",
        description=(
            "Create a base purchase order (not subject to mandate checks). Validates stock, "
            "creates Order + OrderItems, and returns Razorpay test checkout details."
        ),
    )
    async def initiate_purchase(
        buyer_agent_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Initiate a base purchase for the authenticated merchant.

        items: list of {product_id: str, quantity: int}
        """
        merchant_ref = require_merchant_id()
        if isinstance(merchant_ref, dict):
            return merchant_ref

        if not items:
            return error_response("At least one item is required")

        try:
            async with async_session_factory() as db:
                merchant = await resolve_merchant(db, merchant_ref)
                if merchant is None:
                    return error_response("Merchant not found")

                total = Decimal("0.00")
                line_items: list[tuple[Product, int]] = []

                for raw_item in items:
                    product_id = UUID(str(raw_item.get("product_id")))
                    quantity = int(raw_item.get("quantity", 0))
                    if quantity < 1:
                        return error_response("Quantity must be at least 1")

                    product_result = await db.execute(
                        select(Product).where(
                            Product.id == product_id,
                            Product.merchant_id == merchant_ref,
                        )
                    )
                    product = product_result.scalar_one_or_none()
                    if product is None:
                        return error_response(f"Product {product_id} not found")
                    if not product.is_agent_ready:
                        return error_response(f"Product {product.sku} is not agent-ready")
                    if product.stock_quantity < quantity:
                        return error_response(f"Insufficient stock for {product.sku}")

                    total += product.price_inr * quantity
                    line_items.append((product, quantity))

                order = Order(
                    merchant_id=merchant_ref,
                    buyer_agent_id=buyer_agent_id or "demo_agent",
                    razorpay_order_id="pending",
                    status=OrderStatus.created,
                    total_amount_inr=total,
                )
                db.add(order)
                await db.flush()

                for product, quantity in line_items:
                    db.add(
                        OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=quantity,
                            unit_price_inr=product.price_inr,
                        )
                    )

                try:
                    razorpay_order = create_test_order(
                        amount_inr=float(total),
                        receipt_id=str(order.id),
                        merchant=merchant,
                    )
                except RazorpayIntegrationError as exc:
                    await db.rollback()
                    return error_response(str(exc))

                order.razorpay_order_id = razorpay_order["id"]
                await db.commit()

                key_id = merchant.razorpay_key_id
                from app.config import get_settings

                settings = get_settings()
                public_key = key_id or settings.razorpay_key_id

                return {
                    "order_id": str(order.id),
                    "razorpay_order_id": order.razorpay_order_id,
                    "razorpay_key_id": public_key,
                    "amount_inr": float(total),
                    "status": order.status.value,
                }
        except Exception as exc:
            return error_response(f"initiate_purchase failed: {exc}")

    @mcp.tool(
        name="confirm_purchase",
        description=(
            "Verify Razorpay payment signature and finalize order status to paid or failed."
        ),
    )
    async def confirm_purchase(
        order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict[str, Any]:
        """Confirm payment for an order belonging to the authenticated merchant."""
        merchant_ref = require_merchant_id()
        if isinstance(merchant_ref, dict):
            return merchant_ref

        try:
            async with async_session_factory() as db:
                order_uuid = UUID(order_id)
                result = await db.execute(
                    select(Order)
                    .options(selectinload(Order.items))
                    .where(Order.id == order_uuid, Order.merchant_id == merchant_ref)
                )
                order = result.scalar_one_or_none()
                if order is None:
                    return error_response("Order not found")

                if order.status == OrderStatus.paid:
                    return {
                        "order_id": str(order.id),
                        "status": order.status.value,
                        "razorpay_payment_id": order.razorpay_payment_id,
                    }

                merchant = await resolve_merchant(db, merchant_ref)
                if merchant is None:
                    return error_response("Merchant not found")

                try:
                    is_valid = verify_payment_signature(
                        order_id=order.razorpay_order_id,
                        payment_id=razorpay_payment_id,
                        signature=razorpay_signature,
                        merchant=merchant,
                    )
                except RazorpayIntegrationError as exc:
                    return error_response(str(exc))

                if not is_valid:
                    order.status = OrderStatus.failed
                    await db.commit()
                    return {
                        "order_id": str(order.id),
                        "status": order.status.value,
                        "error": "Invalid payment signature",
                    }

                order.razorpay_payment_id = razorpay_payment_id
                order.status = OrderStatus.paid

                for item in order.items:
                    product_result = await db.execute(
                        select(Product).where(Product.id == item.product_id)
                    )
                    product = product_result.scalar_one()
                    product.stock_quantity = max(0, product.stock_quantity - item.quantity)

                await db.commit()
                return {
                    "order_id": str(order.id),
                    "status": order.status.value,
                    "razorpay_payment_id": order.razorpay_payment_id,
                    "total_amount_inr": float(order.total_amount_inr),
                }
        except Exception as exc:
            return error_response(f"confirm_purchase failed: {exc}")
