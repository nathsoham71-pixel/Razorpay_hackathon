from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.mcp.auth import generate_mcp_access_token
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantResponse

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    payload: MerchantCreate,
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """Register a new merchant with optional per-merchant Razorpay test keys."""
    merchant = Merchant(
        business_name=payload.business_name,
        contact_email=payload.contact_email,
        razorpay_key_id=payload.razorpay_key_id,
        razorpay_key_secret=payload.razorpay_key_secret,
        mcp_access_token=generate_mcp_access_token(),
    )
    db.add(merchant)
    await db.flush()
    await db.refresh(merchant)
    return merchant
