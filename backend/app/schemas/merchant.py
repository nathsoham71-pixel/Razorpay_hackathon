from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MerchantCreate(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None


class MerchantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_name: str
    contact_email: str
    created_at: datetime
    razorpay_key_id: str | None = None
    mcp_access_token: str | None = None
