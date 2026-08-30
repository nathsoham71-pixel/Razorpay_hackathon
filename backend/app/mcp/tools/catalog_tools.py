from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import or_, select

from app.db.session import async_session_factory
from app.mcp.tools._helpers import error_response, require_merchant_id
from app.models.product import FeedStatus, Product, ProductFeedVersion


def register_catalog_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_product_feed",
        description=(
            "Return the latest validated ACP/AP2 product feed JSON for the authenticated merchant. "
            "Use this to browse the full agent-ready catalog structure."
        ),
    )
    async def get_product_feed() -> dict[str, Any]:
        """Fetch the latest validated ProductFeedVersion.acp_feed_json for this merchant."""
        merchant_ref = require_merchant_id()
        if isinstance(merchant_ref, dict):
            return merchant_ref

        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ProductFeedVersion)
                    .where(
                        ProductFeedVersion.merchant_id == merchant_ref,
                        ProductFeedVersion.status == FeedStatus.validated,
                    )
                    .order_by(ProductFeedVersion.version_number.desc())
                    .limit(1)
                )
                feed_version = result.scalar_one_or_none()
                if feed_version is None or not feed_version.acp_feed_json:
                    return error_response("No validated product feed found for this merchant")
                return {
                    "feed_version_id": str(feed_version.id),
                    "version_number": feed_version.version_number,
                    "acp_feed_json": feed_version.acp_feed_json,
                }
        except Exception as exc:
            return error_response(f"get_product_feed failed: {exc}")

    @mcp.tool(
        name="search_products",
        description=(
            "Search agent-ready products by title or description (case-insensitive). "
            "Optionally filter by category. Returns id, sku, title, price_inr, category, stock_quantity."
        ),
    )
    async def search_products(
        query: str,
        category: str | None = None,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Simple ILIKE search across is_agent_ready products for the authenticated merchant."""
        merchant_ref = require_merchant_id()
        if isinstance(merchant_ref, dict):
            return merchant_ref

        try:
            async with async_session_factory() as db:
                stmt = select(Product).where(
                    Product.merchant_id == merchant_ref,
                    Product.is_agent_ready.is_(True),
                )
                if query.strip():
                    pattern = f"%{query.strip()}%"
                    stmt = stmt.where(
                        or_(
                            Product.title.ilike(pattern),
                            Product.description.ilike(pattern),
                        )
                    )
                if category:
                    stmt = stmt.where(Product.category.ilike(category.strip()))

                result = await db.execute(stmt.order_by(Product.title.asc()).limit(50))
                products = result.scalars().all()
                return [
                    {
                        "id": str(p.id),
                        "sku": p.sku,
                        "title": p.title,
                        "price_inr": float(p.price_inr),
                        "category": p.category,
                        "stock_quantity": p.stock_quantity,
                    }
                    for p in products
                ]
        except Exception as exc:
            return error_response(f"search_products failed: {exc}")
