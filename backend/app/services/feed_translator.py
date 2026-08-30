from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import FeedStatus, Product, ProductFeedVersion
from app.utils.validators import (
    build_column_map,
    parse_int,
    parse_price,
    parse_str,
)


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            result[str(key)] = None
        elif isinstance(value, (int, float, bool)):
            result[str(key)] = value
        else:
            result[str(key)] = str(value)
    return result


def _validate_row(
    row_index: int,
    row_dict: dict[str, Any],
    column_map: dict[str, str | None],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    extracted: dict[str, Any] = {}

    for field in ("title", "sku", "price"):
        col = column_map.get(field)
        raw_value = row_dict.get(col) if col else None
        if field == "price":
            parsed = parse_price(raw_value)
            if parsed is None:
                errors.append(
                    {
                        "row": row_index,
                        "field": field,
                        "issue": f"Missing or invalid price (column: {col})",
                    }
                )
            else:
                extracted["price_inr"] = parsed
        elif field == "title":
            parsed = parse_str(raw_value)
            if not parsed:
                errors.append(
                    {
                        "row": row_index,
                        "field": field,
                        "issue": f"Missing title (column: {col})",
                    }
                )
            else:
                extracted["title"] = parsed
        elif field == "sku":
            parsed = parse_str(raw_value)
            if not parsed:
                errors.append(
                    {
                        "row": row_index,
                        "field": field,
                        "issue": f"Missing sku (column: {col})",
                    }
                )
            else:
                extracted["sku"] = parsed

    if errors:
        return None, errors

    desc_col = column_map.get("description")
    cat_col = column_map.get("category")
    stock_col = column_map.get("stock")
    image_col = column_map.get("image_url")

    extracted["description"] = parse_str(row_dict.get(desc_col) if desc_col else None)
    extracted["category"] = parse_str(
        row_dict.get(cat_col) if cat_col else None, default="general"
    )
    extracted["stock_quantity"] = parse_int(
        row_dict.get(stock_col) if stock_col else None, default=0
    )
    extracted["image_url"] = parse_str(row_dict.get(image_col) if image_col else None) or None

    return extracted, []


def _build_acp_feed(
    merchant_id: UUID,
    products: list[dict[str, Any]],
) -> dict[str, Any]:
    # TODO: policy fields should be merchant-configurable in a future phase
    return {
        "feed_version": "1.0",
        "merchant_id": str(merchant_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "products": products,
        "policy": {
            "returns_window_days": 7,
            "agent_purchase_allowed": True,
            "requires_mandate": True,
        },
    }


def _product_to_acp_entry(product_data: dict[str, Any]) -> dict[str, Any]:
    stock = product_data.get("stock_quantity", 0)
    return {
        "id": product_data["sku"],
        "title": product_data["title"],
        "description": product_data.get("description", ""),
        "price": {
            "amount": float(product_data["price_inr"]),
            "currency": "INR",
        },
        "availability": "in_stock" if stock > 0 else "out_of_stock",
        "category": product_data.get("category", "general"),
        "agent_purchasable": True,
        "policy_ref": "/policy/default",
    }


async def _next_version_number(db: AsyncSession, merchant_id: UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(ProductFeedVersion.version_number), 0)).where(
            ProductFeedVersion.merchant_id == merchant_id
        )
    )
    current_max = result.scalar_one()
    return int(current_max) + 1


async def translate_feed(
    file_path: str,
    merchant_id: UUID,
    db: AsyncSession,
    raw_feed_filename: str = "upload.csv",
) -> ProductFeedVersion:
    """Translate a messy merchant CSV into an ACP/AP2-style product feed."""
    df = pd.read_csv(file_path, dtype=str, keep_default_na=True)
    df = df.fillna("")

    column_map = build_column_map(list(df.columns))
    version_number = await _next_version_number(db, merchant_id)

    feed_version = ProductFeedVersion(
        merchant_id=merchant_id,
        version_number=version_number,
        raw_feed_filename=raw_feed_filename,
        status=FeedStatus.processing,
        validation_errors=[],
        acp_feed_json=None,
    )
    db.add(feed_version)
    await db.flush()

    all_errors: list[dict[str, Any]] = []
    acp_products: list[dict[str, Any]] = []
    demo_samples: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        row_index = int(idx) + 2  # 1-based + header row
        row_dict = _row_to_dict(row)
        parsed, row_errors = _validate_row(row_index, row_dict, column_map)
        if row_errors:
            all_errors.extend(row_errors)
            continue

        assert parsed is not None
        acp_entry = _product_to_acp_entry(parsed)
        if len(demo_samples) < 2:
            demo_samples.append({"raw": row_dict, "translated": acp_entry})

        existing = await db.execute(
            select(Product).where(
                Product.merchant_id == merchant_id,
                Product.sku == parsed["sku"],
            )
        )
        product = existing.scalar_one_or_none()

        if product is None:
            product = Product(
                merchant_id=merchant_id,
                sku=parsed["sku"],
                title=parsed["title"],
                description=parsed["description"],
                price_inr=parsed["price_inr"],
                currency="INR",
                stock_quantity=parsed["stock_quantity"],
                category=parsed["category"],
                image_url=parsed["image_url"],
                raw_source_row=row_dict,
                is_agent_ready=True,
            )
            db.add(product)
        else:
            product.title = parsed["title"]
            product.description = parsed["description"]
            product.price_inr = parsed["price_inr"]
            product.stock_quantity = parsed["stock_quantity"]
            product.category = parsed["category"]
            product.image_url = parsed["image_url"]
            product.raw_source_row = row_dict
            product.is_agent_ready = True

        acp_products.append(acp_entry)

    acp_feed = _build_acp_feed(merchant_id, acp_products)
    acp_feed["_demo_samples"] = demo_samples
    feed_version.validation_errors = all_errors or None
    feed_version.acp_feed_json = acp_feed
    feed_version.status = FeedStatus.validated if acp_products else FeedStatus.failed

    await db.flush()
    await db.refresh(feed_version)
    return feed_version


def generate_before_after_report(feed_version: ProductFeedVersion) -> dict[str, Any]:
    """Return a before/after comparison for demo visualization."""
    acp_feed = feed_version.acp_feed_json or {}
    acp_products = acp_feed.get("products", [])
    validation_errors = feed_version.validation_errors or []
    failed_rows = {err["row"] for err in validation_errors if "row" in err}

    raw_row_count = len(acp_products) + len(failed_rows)

    return {
        "raw_row_count": raw_row_count,
        "valid_count": len(acp_products),
        "failed_count": len(failed_rows),
        "samples": acp_feed.get("_demo_samples", []),
        "validation_errors_preview": validation_errors[:5],
    }
