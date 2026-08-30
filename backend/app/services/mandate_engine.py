from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mandate import Mandate


@dataclass
class MandateCheckResult:
    approved: bool
    reason: str
    mandate_id: UUID | None
    max_allowed_inr: Decimal | None


async def get_active_mandate(db: AsyncSession, merchant_id: UUID) -> Mandate | None:
    """Return the active mandate for a merchant, if one exists."""
    result = await db.execute(
        select(Mandate).where(
            Mandate.merchant_id == merchant_id,
            Mandate.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def check_upsell_against_mandate(
    db: AsyncSession,
    merchant_id: UUID,
    proposed_item_category: str,
    proposed_item_price_inr: Decimal,
    requested_field_changes: list[str],
) -> MandateCheckResult:
    """
    Deterministic mandate enforcement — no GPT, no Razorpay, no side effects beyond DB read.

    Single source of truth for upsell spend authorization.
    """
    mandate = await get_active_mandate(db, merchant_id)
    if mandate is None:
        return MandateCheckResult(
            approved=False,
            reason="no_active_mandate",
            mandate_id=None,
            max_allowed_inr=None,
        )

    if proposed_item_category not in mandate.allowed_categories:
        return MandateCheckResult(
            approved=False,
            reason="category_not_allowed",
            mandate_id=mandate.id,
            max_allowed_inr=mandate.max_upsell_amount_inr,
        )

    if proposed_item_price_inr > mandate.max_upsell_amount_inr:
        return MandateCheckResult(
            approved=False,
            reason="exceeds_spend_limit",
            mandate_id=mandate.id,
            max_allowed_inr=mandate.max_upsell_amount_inr,
        )

    locked = set(mandate.locked_fields or [])
    for field in requested_field_changes:
        if field in locked:
            return MandateCheckResult(
                approved=False,
                reason="locked_field_violation",
                mandate_id=mandate.id,
                max_allowed_inr=mandate.max_upsell_amount_inr,
            )

    return MandateCheckResult(
        approved=True,
        reason="within_mandate",
        mandate_id=mandate.id,
        max_allowed_inr=mandate.max_upsell_amount_inr,
    )
