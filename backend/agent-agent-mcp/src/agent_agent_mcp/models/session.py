from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agent_agent_mcp.models.a2a import A2APayload


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ConversationSession(BaseModel):
    session_id: str
    agent_id: str
    merchant_id: str

    status: SessionStatus = SessionStatus.ACTIVE

    conversation_history: list[A2APayload] = Field(
        default_factory=list
    )

    cart_state: dict[str, Any] = Field(
        default_factory=dict
    )

    active_order: dict[str, Any] | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    last_active: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def touch(self) -> None:
        self.last_active = datetime.now(timezone.utc)

    def add_turn(self, payload: A2APayload) -> None:
        self.conversation_history.append(payload)
        self.touch()