from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    merchant_id: UUID
    buyer_agent_id: str = Field(default="demo_agent", min_length=1)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderVerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_signature: str


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    unit_price_inr: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    buyer_agent_id: str
    razorpay_order_id: str
    razorpay_payment_id: str | None
    status: str
    total_amount_inr: Decimal
    created_at: datetime
    items: list[OrderItemResponse] = Field(default_factory=list)


class OrderCreateResponse(BaseModel):
    order: OrderResponse
    razorpay_order: dict
