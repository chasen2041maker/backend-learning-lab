from __future__ import annotations

from uuid import UUID


class DomainError(Exception):
    code = "domain_error"


class AuthenticationRequired(DomainError):
    code = "authentication_required"


class TicketNotFound(DomainError):
    code = "ticket_not_found"

    def __init__(self, ticket_id: UUID) -> None:
        super().__init__(f"ticket {ticket_id} does not exist")


class TicketStateConflict(DomainError):
    code = "ticket_state_conflict"


class TicketVersionConflict(DomainError):
    code = "ticket_version_conflict"
