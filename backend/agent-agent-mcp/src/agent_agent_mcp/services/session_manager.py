from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from agent_agent_mcp.models.session import (
    ConversationSession,
    SessionStatus,
)


logger = logging.getLogger(__name__)


class SessionNotFoundError(Exception):
    pass


class SessionManager:
    """
    Application-level conversation session manager.

    This is intentionally separate from MCP's own transport session.
    """

    def __init__(
        self,
        ttl_seconds: int = 1800,
        cleanup_interval_seconds: int = 300,
    ):
        self._sessions: dict[str, ConversationSession] = {}

        self._lock = asyncio.Lock()

        self._ttl = timedelta(seconds=ttl_seconds)
        self._cleanup_interval = cleanup_interval_seconds

        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop()
        )

        logger.info("Session manager started")

    async def stop(self) -> None:
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()

            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

            self._cleanup_task = None

        async with self._lock:
            self._sessions.clear()

        logger.info("Session manager stopped")

    async def create(
        self,
        agent_id: str,
        merchant_id: str,
        session_id: str | None = None,
    ) -> ConversationSession:

        session_id = session_id or str(uuid4())

        session = ConversationSession(
            session_id=session_id,
            agent_id=agent_id,
            merchant_id=merchant_id,
        )

        async with self._lock:
            self._sessions[session_id] = session

        return session

    async def get(
        self,
        session_id: str,
    ) -> ConversationSession:

        async with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                raise SessionNotFoundError(
                    f"Session '{session_id}' does not exist"
                )

            if session.status == SessionStatus.EXPIRED:
                raise SessionNotFoundError(
                    f"Session '{session_id}' has expired"
                )

            session.touch()

            return session

    async def get_or_create(
        self,
        session_id: str,
        agent_id: str,
        merchant_id: str,
    ) -> ConversationSession:

        async with self._lock:
            session = self._sessions.get(session_id)

            if session is not None:
                if (
                    session.agent_id != agent_id
                    or session.merchant_id != merchant_id
                ):
                    raise PermissionError(
                        "Session does not belong to the supplied agent "
                        "and merchant."
                    )

                if session.status == SessionStatus.EXPIRED:
                    raise SessionNotFoundError(
                        f"Session '{session_id}' has expired"
                    )

                session.touch()
                return session

            session = ConversationSession(
                session_id=session_id,
                agent_id=agent_id,
                merchant_id=merchant_id,
            )

            self._sessions[session_id] = session

            return session

    async def update(
        self,
        session: ConversationSession,
    ) -> None:

        session.touch()

        async with self._lock:
            self._sessions[session.session_id] = session

    async def delete(
        self,
        session_id: str,
    ) -> None:

        async with self._lock:
            self._sessions.pop(session_id, None)

    async def _cleanup_loop(self) -> None:

        while self._running:

            try:
                await asyncio.sleep(self._cleanup_interval)

                now = datetime.now(timezone.utc)

                async with self._lock:

                    expired_ids = [
                        session_id
                        for session_id, session
                        in self._sessions.items()
                        if now - session.last_active > self._ttl
                    ]

                    for session_id in expired_ids:
                        session = self._sessions[session_id]
                        session.status = SessionStatus.EXPIRED

                        del self._sessions[session_id]

                    if expired_ids:
                        logger.info(
                            "Purged %d expired sessions",
                            len(expired_ids),
                        )

            except asyncio.CancelledError:
                raise

            except Exception:
                logger.exception(
                    "Unexpected error in session cleanup loop"
                )