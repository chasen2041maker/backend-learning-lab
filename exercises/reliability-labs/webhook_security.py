from __future__ import annotations

import hashlib
import hmac
import time


class InvalidWebhook(Exception):
    pass


def signature(secret: bytes, timestamp: int, raw_body: bytes) -> str:
    message = str(timestamp).encode() + b"." + raw_body
    return "sha256=" + hmac.new(secret, message, hashlib.sha256).hexdigest()


class WebhookVerifier:
    def __init__(self, secret: bytes, *, tolerance_seconds: int = 300) -> None:
        self._secret = secret
        self._tolerance = tolerance_seconds
        self._processed_event_ids: set[str] = set()

    def verify_and_record(
        self,
        *,
        event_id: str,
        timestamp: int,
        raw_body: bytes,
        supplied_signature: str,
        now: int | None = None,
    ) -> bool:
        current = int(time.time()) if now is None else now
        if abs(current - timestamp) > self._tolerance:
            raise InvalidWebhook("timestamp outside replay window")
        expected = signature(self._secret, timestamp, raw_body)
        if not hmac.compare_digest(expected, supplied_signature):
            raise InvalidWebhook("signature mismatch")
        if event_id in self._processed_event_ids:
            return False
        self._processed_event_ids.add(event_id)
        return True
