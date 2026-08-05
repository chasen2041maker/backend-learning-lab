from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from starter.observations import classify_result, request_ids_match


def test_transport_failure_is_not_an_http_status() -> None:
    assert classify_result(status_code=None, code=None) == "network_error"


def test_api_errors_keep_their_stable_code() -> None:
    assert classify_result(status_code=400, code="invalid_json") == "invalid_json"
    assert (
        classify_result(status_code=401, code="authentication_required")
        == "authentication_required"
    )
    assert (
        classify_result(status_code=404, code="ticket_not_found") == "ticket_not_found"
    )
    assert (
        classify_result(status_code=422, code="invalid_ticket_input")
        == "invalid_ticket_input"
    )


def test_request_id_must_match_between_header_and_body() -> None:
    assert request_ids_match("req_lesson_001", {"request_id": "req_lesson_001"})
    assert not request_ids_match("req_header", {"request_id": "req_body"})
