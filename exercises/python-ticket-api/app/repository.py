from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from .errors import TicketVersionConflict
from .models import Ticket, TicketStatus


class TicketRepository(Protocol):
    async def create(self, ticket: Ticket) -> Ticket: ...

    async def get(self, tenant_id: str, ticket_id: UUID) -> Ticket | None: ...

    async def list_for_tenant(self, tenant_id: str) -> Sequence[Ticket]: ...

    async def set_status(
        self,
        tenant_id: str,
        ticket_id: UUID,
        status: TicketStatus,
        expected_version: int,
    ) -> Ticket | None: ...


class InMemoryTicketRepository:
    """A deterministic learning fake, not a production database."""

    def __init__(self) -> None:
        self._tickets: dict[UUID, Ticket] = {}
        self._lock = asyncio.Lock()

    async def create(self, ticket: Ticket) -> Ticket:
        async with self._lock:
            self._tickets[ticket.id] = ticket
            return ticket

    async def get(self, tenant_id: str, ticket_id: UUID) -> Ticket | None:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if ticket is None or ticket.tenant_id != tenant_id:
                return None
            return ticket

    async def list_for_tenant(self, tenant_id: str) -> Sequence[Ticket]:
        async with self._lock:
            result = [ticket for ticket in self._tickets.values() if ticket.tenant_id == tenant_id]
            return tuple(sorted(result, key=lambda item: (item.created_at, item.id), reverse=True))

    async def set_status(
        self,
        tenant_id: str,
        ticket_id: UUID,
        status: TicketStatus,
        expected_version: int,
    ) -> Ticket | None:
        async with self._lock:
            current = self._tickets.get(ticket_id)
            if current is None or current.tenant_id != tenant_id:
                return None
            if current.version != expected_version:
                raise TicketVersionConflict(
                    f"expected version {expected_version}, current version {current.version}"
                )
            updated = current.model_copy(
                update={
                    "status": status,
                    "version": current.version + 1,
                    "updated_at": datetime.now(UTC),
                }
            )
            self._tickets[ticket_id] = updated
            return updated
