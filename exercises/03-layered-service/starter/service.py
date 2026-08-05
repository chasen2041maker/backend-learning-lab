from __future__ import annotations

from .repository import TicketRepository


class TicketNotFound(Exception):
    pass


class TicketStateConflict(Exception):
    pass


class TicketVersionConflict(Exception):
    pass


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repository = repository

    async def close(
        self, tenant_id: str, ticket_id: str, expected_version: int
    ) -> dict[str, object]:
        """Close one ticket.

        TODO: move the state, tenant, and version rules out of api.close_ticket,
        then save the updated ticket through the injected repository.
        """
        raise NotImplementedError
