import os
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.product import Product, ProductFeedVersion
from app.schemas.product import FeedUploadResponse, ProductFeedVersionResponse, ProductResponse
from app.services.feed_translator import generate_before_after_report, translate_feed

router = APIRouter(prefix="/merchants", tags=["feed"])


async def _get_merchant_or_404(merchant_id: UUID, db: AsyncSession) -> Merchant:
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return merchant


@router.post(
    "/{merchant_id}/feed/upload",
    response_model=FeedUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_feed(
    merchant_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> FeedUploadResponse:
    """Upload a CSV product feed and translate it to ACP/AP2-style JSON."""
    await _get_merchant_or_404(merchant_id, db)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
        )

    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    temp_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{file.filename}")

    content = await file.read()
    with open(temp_path, "wb") as handle:
        handle.write(content)

    try:
        feed_version = await translate_feed(
            file_path=temp_path,
            merchant_id=merchant_id,
            db=db,
            raw_feed_filename=file.filename,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    report = generate_before_after_report(feed_version)
    return FeedUploadResponse(
        feed_version=ProductFeedVersionResponse.model_validate(feed_version),
        before_after_report=report,
    )


@router.get(
    "/{merchant_id}/feed/{version_id}",
    response_model=ProductFeedVersionResponse,
)
async def get_feed_version(
    merchant_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ProductFeedVersion:
    """Fetch a specific product feed version for a merchant."""
    await _get_merchant_or_404(merchant_id, db)

    result = await db.execute(
        select(ProductFeedVersion).where(
            ProductFeedVersion.id == version_id,
            ProductFeedVersion.merchant_id == merchant_id,
        )
    )
    feed_version = result.scalar_one_or_none()
    if feed_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed version not found")
    return feed_version


@router.get("/{merchant_id}/products", response_model=list[ProductResponse])
async def list_products(
    merchant_id: UUID,
    is_agent_ready: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[Product]:
    """List products for a merchant, optionally filtered by agent-readiness."""
    await _get_merchant_or_404(merchant_id, db)

    query = select(Product).where(Product.merchant_id == merchant_id)
    if is_agent_ready is not None:
        query = query.where(Product.is_agent_ready == is_agent_ready)

    result = await db.execute(query.order_by(Product.created_at.desc()))
    return list(result.scalars().all())
