import uuid
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.mandate import Mandate
from app.models.merchant import Merchant
from app.services.mandate_engine import check_upsell_against_mandate

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def mandate_test_context() -> AsyncGenerator[tuple[AsyncSession, uuid.UUID], None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    merchant_id = uuid.uuid4()
    mandate_id = uuid.uuid4()

    async with session_factory() as session:
        merchant = Merchant(
            id=merchant_id,
            business_name="Mandate Test Store",
            contact_email="mandate-test@example.com",
            mcp_access_token=f"test-token-{uuid.uuid4()}",
        )
        mandate = Mandate(
            id=mandate_id,
            merchant_id=merchant_id,
            name="default_upsell_mandate",
            max_upsell_amount_inr=Decimal("500.00"),
            allowed_categories=["electronics", "accessories"],
            locked_fields=["shipping_address"],
            is_active=True,
        )
        session.add(merchant)
        session.add(mandate)
        await session.commit()

        yield session, merchant_id

        await session.delete(mandate)
        await session.delete(merchant)
        await session.commit()

    await engine.dispose()


async def test_no_active_mandate(mandate_test_context) -> None:
    from sqlalchemy import update

    db_session, merchant_id = mandate_test_context
    await db_session.execute(
        update(Mandate).where(Mandate.merchant_id == merchant_id).values(is_active=False)
    )
    await db_session.commit()

    result = await check_upsell_against_mandate(
        db=db_session,
        merchant_id=merchant_id,
        proposed_item_category="electronics",
        proposed_item_price_inr=Decimal("100.00"),
        requested_field_changes=[],
    )
    assert result.approved is False
    assert result.reason == "no_active_mandate"


async def test_category_not_allowed(mandate_test_context) -> None:
    db_session, merchant_id = mandate_test_context
    result = await check_upsell_against_mandate(
        db=db_session,
        merchant_id=merchant_id,
        proposed_item_category="furniture",
        proposed_item_price_inr=Decimal("100.00"),
        requested_field_changes=[],
    )
    assert result.approved is False
    assert result.reason == "category_not_allowed"


async def test_exceeds_spend_limit(mandate_test_context) -> None:
    db_session, merchant_id = mandate_test_context
    result = await check_upsell_against_mandate(
        db=db_session,
        merchant_id=merchant_id,
        proposed_item_category="electronics",
        proposed_item_price_inr=Decimal("999.00"),
        requested_field_changes=[],
    )
    assert result.approved is False
    assert result.reason == "exceeds_spend_limit"
    assert result.max_allowed_inr == Decimal("500.00")


async def test_locked_field_violation(mandate_test_context) -> None:
    db_session, merchant_id = mandate_test_context
    result = await check_upsell_against_mandate(
        db=db_session,
        merchant_id=merchant_id,
        proposed_item_category="electronics",
        proposed_item_price_inr=Decimal("100.00"),
        requested_field_changes=["shipping_address"],
    )
    assert result.approved is False
    assert result.reason == "locked_field_violation"


async def test_within_mandate(mandate_test_context) -> None:
    db_session, merchant_id = mandate_test_context
    result = await check_upsell_against_mandate(
        db=db_session,
        merchant_id=merchant_id,
        proposed_item_category="accessories",
        proposed_item_price_inr=Decimal("299.00"),
        requested_field_changes=[],
    )
    assert result.approved is True
    assert result.reason == "within_mandate"
    assert result.max_allowed_inr == Decimal("500.00")
