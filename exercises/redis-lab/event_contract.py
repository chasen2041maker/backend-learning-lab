from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


class InvalidEvent(ValueError):
    """The event is not a valid v1 envelope."""


class UnsupportedEventVersion(InvalidEvent):
    """The envelope is valid JSON but has no supported event version."""


@dataclass(frozen=True)
class TicketClosedV1Payload:
    ticket_id: str
    status: Literal["closed"]
    version: int


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    event_version: int
    occurred_at: datetime
    tenant_id: str
    request_id: str
    trace_id: str
    payload: TicketClosedV1Payload


SUPPORTED_EVENT_VERSIONS = {"ticket.closed": frozenset({1})}
REQUIRED_FIELDS = frozenset(
    {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "tenant_id",
        "request_id",
        "trace_id",
        "payload",
    }
)
TICKET_CLOSED_V1_FIELDS = frozenset({"ticket_id", "status", "version"})
UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def parse_supported_event(raw: str) -> EventEnvelope:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidEvent("event is not valid JSON") from exc
    if not isinstance(value, dict):
        raise InvalidEvent("event envelope must be an object")

    missing = REQUIRED_FIELDS - value.keys()
    if missing:
        raise InvalidEvent(f"event is missing required fields: {sorted(missing)}")

    event_id = value["event_id"]
    event_type = value["event_type"]
    event_version = value["event_version"]
    occurred_at = value["occurred_at"]
    tenant_id = value["tenant_id"]
    request_id = value["request_id"]
    trace_id = value["trace_id"]
    payload = value["payload"]

    if not isinstance(event_id, str) or not _is_uuid(event_id):
        raise InvalidEvent("event_id must be a UUID string")
    if not isinstance(event_type, str) or not event_type:
        raise InvalidEvent("event_type must be a non-empty string")
    if (
        not isinstance(event_version, int)
        or isinstance(event_version, bool)
        or event_version < 1
    ):
        raise InvalidEvent("event_version must be a positive integer")
    if not isinstance(occurred_at, str):
        raise InvalidEvent("occurred_at must be an ISO-8601 timestamp")
    try:
        parsed_occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidEvent("occurred_at must be an ISO-8601 timestamp") from exc
    if parsed_occurred_at.tzinfo is None:
        raise InvalidEvent("occurred_at must include a timezone")
    if not isinstance(tenant_id, str) or not 1 <= len(tenant_id) <= 64:
        raise InvalidEvent("tenant_id must contain 1 to 64 characters")
    if not isinstance(request_id, str) or not request_id:
        raise InvalidEvent("request_id must be a non-empty string")
    if not isinstance(trace_id, str) or not trace_id:
        raise InvalidEvent("trace_id must be a non-empty string")
    if not isinstance(payload, dict):
        raise InvalidEvent("payload must be an object")

    supported_versions = SUPPORTED_EVENT_VERSIONS.get(event_type)
    if supported_versions is None or event_version not in supported_versions:
        raise UnsupportedEventVersion(
            f"unsupported event version: {event_type} v{event_version}"
        )

    parsed_payload = _parse_ticket_closed_v1_payload(payload)

    return EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        event_version=event_version,
        occurred_at=parsed_occurred_at,
        tenant_id=tenant_id,
        request_id=request_id,
        trace_id=trace_id,
        payload=parsed_payload,
    )


def _parse_ticket_closed_v1_payload(
    payload: dict[str, object],
) -> TicketClosedV1Payload:
    fields = frozenset(payload)
    if fields != TICKET_CLOSED_V1_FIELDS:
        missing = sorted(TICKET_CLOSED_V1_FIELDS - fields)
        extra = sorted(fields - TICKET_CLOSED_V1_FIELDS)
        raise InvalidEvent(
            f"ticket.closed v1 payload fields are invalid: missing={missing}, extra={extra}"
        )
    ticket_id = payload["ticket_id"]
    status = payload["status"]
    version = payload["version"]
    if not isinstance(ticket_id, str) or UUID_V4_PATTERN.fullmatch(ticket_id) is None:
        raise InvalidEvent("ticket.closed v1 ticket_id must be a canonical UUID v4")
    if status != "closed":
        raise InvalidEvent("ticket.closed v1 status must be closed")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise InvalidEvent("ticket.closed v1 version must be a positive integer")
    return TicketClosedV1Payload(ticket_id=ticket_id, status="closed", version=version)


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True
