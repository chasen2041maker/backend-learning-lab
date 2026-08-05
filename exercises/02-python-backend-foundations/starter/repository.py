from __future__ import annotations

from typing import Protocol

from .models import Ticket


class TicketRepository(Protocol):
    async def create(self, ticket: Ticket) -> Ticket: ...


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    async def create(self, ticket: Ticket) -> Ticket:
        self._tickets[str(ticket.id)] = ticket
        return ticket
