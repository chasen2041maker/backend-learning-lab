from __future__ import annotations

from typing import Protocol


class TicketRepository(Protocol):
    async def get(self, tenant_id: str, ticket_id: str) -> dict[str, object] | None: ...

    async def save(
        self, tenant_id: str, ticket_id: str, ticket: dict[str, object]
    ) -> dict[str, object]: ...


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self._tickets = {
            "ticket-1": {"tenant_id": "tenant_a", "status": "open", "version": 1}
        }

    async def get(self, tenant_id: str, ticket_id: str) -> dict[str, object] | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None or ticket["tenant_id"] != tenant_id:
            return None
        return dict(ticket)

    async def save(
        self, tenant_id: str, ticket_id: str, ticket: dict[str, object]
    ) -> dict[str, object]:
        if ticket.get("tenant_id") != tenant_id:
            raise ValueError("tenant mismatch")
        self._tickets[ticket_id] = dict(ticket)
        return dict(ticket)
