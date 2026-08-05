from __future__ import annotations

from .models import CloseTicket

TICKETS = {"ticket-1": {"tenant_id": "tenant_a", "status": "open", "version": 1}}


def close_ticket(
    ticket_id: str, body: dict[str, object], tenant_id: str = "tenant_a"
) -> dict[str, object]:
    """Initial all-in-one handler used to expose the testing problem."""
    command = CloseTicket.model_validate(body)
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["tenant_id"] != tenant_id:
        return {"status": 404, "code": "ticket_not_found"}
    if ticket["status"] == "closed":
        return {"status": 409, "code": "ticket_state_conflict"}
    if ticket["version"] != command.expected_version:
        return {"status": 409, "code": "ticket_version_conflict"}
    ticket["status"] = "closed"
    ticket["version"] = int(ticket["version"]) + 1
    return {"status": 200, "code": "ok", "data": dict(ticket)}
