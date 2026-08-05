from __future__ import annotations

from .models import Ticket, TicketCreate
from .repository import TicketRepository


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repository = repository

    async def create(self, tenant_id: str, command: TicketCreate) -> Ticket:
        ticket = Ticket.new(command, tenant_id)
        return await self._repository.create(ticket)
