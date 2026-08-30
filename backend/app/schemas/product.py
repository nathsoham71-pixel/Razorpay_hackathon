from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    sku: str
    title: str
    description: str
    price_inr: Decimal
    currency: str
    stock_quantity: int
    category: str
    image_url: str | None
    is_agent_ready: bool
    created_at: datetime
    updated_at: datetime


class ProductFeedVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    version_number: int
    uploaded_at: datetime
    raw_feed_filename: str
    status: str
    validation_errors: list[dict[str, Any]] | None
    acp_feed_json: dict[str, Any] | None


class FeedUploadResponse(BaseModel):
    feed_version: ProductFeedVersionResponse
    before_after_report: dict[str, Any]


class BeforeAfterReport(BaseModel):
    raw_row_count: int
    valid_count: int
    failed_count: int
    samples: list[dict[str, Any]] = Field(default_factory=list)
