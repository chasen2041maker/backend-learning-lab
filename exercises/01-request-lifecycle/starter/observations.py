from __future__ import annotations


def classify_result(*, status_code: int | None, code: str | None) -> str:
    """Classify one recorded request result.

    TODO: distinguish a transport failure from an HTTP response, then preserve
    the stable API error code for HTTP failures.
    """
    raise NotImplementedError


def request_ids_match(response_header: str, response_body: dict[str, object]) -> bool:
    """Return whether the response header and envelope carry the same ID.

    TODO: read request_id from response_body and compare it with the header.
    """
    raise NotImplementedError
