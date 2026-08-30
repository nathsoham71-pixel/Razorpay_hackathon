from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    OrderResponse,
    OrderVerifyRequest,
)
from app.services.razorpay_client import (
    RazorpayIntegrationError,
    create_test_order,
    verify_payment_signature,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderCreateResponse:
    """Create an order and a corresponding Razorpay test-mode order."""
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == payload.merchant_id)
    )
    merchant = merchant_result.scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    total = Decimal("0.00")
    line_items: list[tuple[Product, int]] = []

    for item in payload.items:
        product_result = await db.execute(
            select(Product).where(
                Product.id == item.product_id,
                Product.merchant_id == payload.merchant_id,
            )
        )
        product = product_result.scalar_one_or_none()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found for merchant",
            )
        if not product.is_agent_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product.sku} is not agent-ready",
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.sku}",
            )
        line_total = product.price_inr * item.quantity
        total += line_total
        line_items.append((product, item.quantity))

    order = Order(
        merchant_id=payload.merchant_id,
        buyer_agent_id=payload.buyer_agent_id,
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    order.razorpay_order_id = razorpay_order["id"]
    await db.flush()

    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    )
    order = result.scalar_one()

    return OrderCreateResponse(
        order=OrderResponse.model_validate(order),
        razorpay_order=razorpay_order,
    )


@router.post("/{order_id}/verify", response_model=OrderResponse)
async def verify_order_payment(
    order_id: UUID,
    payload: OrderVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Verify Razorpay payment signature and finalize the order with line items."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status == OrderStatus.paid:
        return order

    merchant_result = await db.execute(select(Merchant).where(Merchant.id == order.merchant_id))
    merchant = merchant_result.scalar_one()

    try:
        is_valid = verify_payment_signature(
            order_id=order.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            signature=payload.razorpay_signature,
            merchant=merchant,
        )
    except RazorpayIntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if not is_valid:
        order.status = OrderStatus.failed
        await db.flush()
        await db.refresh(order)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature",
        )

    order.razorpay_payment_id = payload.razorpay_payment_id
    order.status = OrderStatus.paid

    if not order.items:
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        order.items = list(items_result.scalars().all())

    for item in order.items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one()
        product.stock_quantity = max(0, product.stock_quantity - item.quantity)

    await db.flush()
    await db.refresh(order)
    return order
