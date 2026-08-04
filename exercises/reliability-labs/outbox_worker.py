from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4


class OutboxState(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    DEAD = "dead"


@dataclass
class OutboxEvent:
    id: UUID
    state: OutboxState = OutboxState.PENDING
    attempts: int = 0
    next_attempt_at: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )
    locked_by: str | None = None
    locked_until: datetime | None = None
    lease_token: int = 0
    last_error: str | None = None


class InMemoryOutbox:
    """Deterministic model of the SQL protocol; not a database replacement."""

    def __init__(self) -> None:
        self.events: dict[UUID, OutboxEvent] = {}

    def add(self) -> OutboxEvent:
        event = OutboxEvent(id=uuid4())
        self.events[event.id] = event
        return event

    def claim(
        self, worker: str, now: datetime, *, lease_seconds: int = 30
    ) -> OutboxEvent | None:
        for event in self.events.values():
            lease_expired = event.locked_until is None or event.locked_until <= now
            if (
                event.state is OutboxState.PENDING
                and event.next_attempt_at <= now
                and lease_expired
            ):
                event.locked_by = worker
                event.locked_until = now + timedelta(seconds=lease_seconds)
                event.lease_token += 1
                return event
        return None

    def mark_published(self, event_id: UUID, worker: str, lease_token: int) -> bool:
        event = self.events[event_id]
        if event.locked_by != worker or event.lease_token != lease_token:
            return False
        event.state = OutboxState.PUBLISHED
        event.locked_by = None
        event.locked_until = None
        return True

    def mark_failed(
        self,
        event_id: UUID,
        worker: str,
        lease_token: int,
        now: datetime,
        error: str,
        *,
        max_attempts: int = 3,
    ) -> bool:
        event = self.events[event_id]
        if event.locked_by != worker or event.lease_token != lease_token:
            return False
        event.attempts += 1
        event.last_error = error[:500]
        event.locked_by = None
        event.locked_until = None
        if event.attempts >= max_attempts:
            event.state = OutboxState.DEAD
        else:
            delay = min(300, 2 ** (event.attempts - 1))
            event.next_attempt_at = now + timedelta(seconds=delay)
        return True
