from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from .errors import (
    TicketNotFound,
    TicketStateConflict,
)
from .models import Ticket, TicketCreate, TicketStatus
from .repository import TicketRepository


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repository = repository

    async def create(self, tenant_id: str, command: TicketCreate) -> Ticket:
        ticket = Ticket.new(command, tenant_id)
        return await self._repository.create(ticket)

    async def get(self, ticket_id: UUID, tenant_id: str) -> Ticket:
        ticket = await self._repository.get(tenant_id, ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)
        return ticket

    async def list_for_tenant(self, tenant_id: str) -> Sequence[Ticket]:
        return await self._repository.list_for_tenant(tenant_id)

    async def close(self, ticket_id: UUID, tenant_id: str, expected_version: int) -> Ticket:
        current = await self.get(ticket_id, tenant_id)
        if current.status is TicketStatus.CLOSED:
            raise TicketStateConflict("ticket is already closed")
        updated = await self._repository.set_status(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            status=TicketStatus.CLOSED,
            expected_version=expected_version,
        )
        if updated is None:
            raise TicketNotFound(ticket_id)
        return updated
