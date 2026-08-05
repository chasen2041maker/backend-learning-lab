from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from starter import api


def test_all_in_one_handler_leaks_state_between_calls() -> None:
    api.TICKETS["ticket-1"] = {
        "tenant_id": "tenant_a",
        "status": "open",
        "version": 1,
    }

    first = api.close_ticket("ticket-1", {"expected_version": 1})
    second = api.close_ticket("ticket-1", {"expected_version": 1})

    assert first["status"] == 200
    assert second == {"status": 409, "code": "ticket_state_conflict"}
