from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    CLAUDE_AGENT = "claude_agent"
    MERCHANT_AGENT = "merchant_agent"


class A2AAction(str, Enum):
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    ORDER_INTENT = "ORDER_INTENT"
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    ERROR = "ERROR"


class A2AHeader(BaseModel):
    session_id: str = Field(min_length=1)
    sender: AgentRole
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    action: A2AAction


class A2ABody(BaseModel):
    intent: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    text_summary: str


class A2APayload(BaseModel):
    header: A2AHeader
    body: A2ABody