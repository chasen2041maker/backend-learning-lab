from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
from collections.abc import Callable


class InvalidWebhook(Exception):
    pass


def signature(secret: bytes, timestamp: int, raw_body: bytes) -> str:
    message = str(timestamp).encode() + b"." + raw_body
    return "sha256=" + hmac.new(secret, message, hashlib.sha256).hexdigest()


class WebhookVerifier:
    def __init__(self, secret: bytes, *, tolerance_seconds: int = 300) -> None:
        self._secret = secret
        self._tolerance = tolerance_seconds

    def verify_and_extract_event_id(
        self,
        *,
        timestamp: int,
        raw_body: bytes,
        supplied_signature: str,
        now: int | None = None,
    ) -> str:
        current = int(time.time()) if now is None else now
        if abs(current - timestamp) > self._tolerance:
            raise InvalidWebhook("timestamp outside replay window")
        expected = signature(self._secret, timestamp, raw_body)
        if not hmac.compare_digest(expected, supplied_signature):
            raise InvalidWebhook("signature mismatch")
        try:
            payload = json.loads(raw_body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidWebhook("body is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise InvalidWebhook("body must be a JSON object")
        event_id = payload.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise InvalidWebhook("body event_id must be a non-empty string")
        return event_id


class WebhookProcessor:
    """In-memory teaching model; production uses a database transaction."""

    def __init__(self) -> None:
        self._applied_event_ids: set[str] = set()
        self._lock = threading.Lock()

    def process_once(self, event_id: str, effect: Callable[[], None]) -> bool:
        with self._lock:
            if event_id in self._applied_event_ids:
                return False
            effect()
            self._applied_event_ids.add(event_id)
            return True
