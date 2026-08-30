import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.mandate import Mandate
    from app.models.order import Order
    from app.models.product import Product, ProductFeedVersion


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # encrypt in production — plain text acceptable for this demo
    razorpay_key_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_key_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mcp_access_token: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    products: Mapped[list["Product"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    feed_versions: Mapped[list["ProductFeedVersion"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    mandates: Mapped[list["Mandate"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
