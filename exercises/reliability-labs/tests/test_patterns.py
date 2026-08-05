from __future__ import annotations

import asyncio
import sys
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[2] / "redis-lab"))

from authorization import ForbiddenError, Principal, ToolCall, authorize_tool_call
from concurrency_timeout import run_bounded
from event_contract import InvalidEvent, UnsupportedEventVersion, parse_supported_event
from fake_rag import Document, answer_with_fake_rag
from outbox_worker import InMemoryOutbox, OutboxState
from webhook_security import InvalidWebhook, WebhookVerifier, signature


class ReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrency_timeout_is_bounded(self) -> None:
        active = 0
        peak = 0

        async def call(delay: float) -> str:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(delay)
                return "ok"
            finally:
                active -= 1

        results = await run_bounded(
            {
                "a": lambda: call(0.01),
                "b": lambda: call(0.01),
                "slow": lambda: call(0.2),
            },
            max_concurrency=2,
            per_call_timeout_seconds=0.05,
            total_timeout_seconds=0.5,
        )
        self.assertLessEqual(peak, 2)
        self.assertEqual(results["slow"].error, "timeout")

    async def test_concurrency_timeout_has_total_deadline_and_cancels_queued_work(
        self,
    ) -> None:
        started = 0
        cancelled = 0

        async def slow_call() -> str:
            nonlocal started, cancelled
            started += 1
            try:
                await asyncio.sleep(1)
                return "ok"
            finally:
                cancelled += 1

        started_at = time.monotonic()
        results = await run_bounded(
            {str(index): slow_call for index in range(10)},
            max_concurrency=1,
            per_call_timeout_seconds=0.2,
            total_timeout_seconds=0.08,
        )
        elapsed = time.monotonic() - started_at

        self.assertLess(elapsed, 0.2)
        self.assertEqual(set(results), {str(index) for index in range(10)})
        self.assertTrue(
            all(result.error == "deadline_exceeded" for result in results.values())
        )
        self.assertEqual(started, 1)
        self.assertEqual(cancelled, 1)

    async def test_agent_side_effect_needs_permission_confirmation_and_idempotency(
        self,
    ) -> None:
        principal = Principal("user_a", "tenant_a", frozenset({"ticket:write"}))
        authorize_tool_call(
            principal,
            ToolCall(
                "ticket.close", "tenant_a", confirmed=True, idempotency_key="close-1"
            ),
        )
        with self.assertRaises(ForbiddenError):
            authorize_tool_call(
                principal, ToolCall("ticket.close", "tenant_b", confirmed=True)
            )

    async def test_webhook_uses_raw_bytes_window_and_dedup(self) -> None:
        secret = b"local-test-secret"
        raw = b'{"event_id":"evt_1"}'
        verifier = WebhookVerifier(secret)
        supplied = signature(secret, 1_000, raw)
        self.assertTrue(
            verifier.verify_and_record(
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=1_001,
            )
        )
        self.assertFalse(
            verifier.verify_and_record(
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=1_001,
            )
        )
        changed_body = b'{"event_id":"evt_2"}'
        with self.assertRaises(InvalidWebhook):
            verifier.verify_and_record(
                timestamp=1_000,
                raw_body=changed_body,
                supplied_signature=supplied,
                now=1_001,
            )
        with self.assertRaises(InvalidWebhook):
            verifier.verify_and_record(
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=2_000,
            )

    async def test_event_contract_rejects_invalid_and_unknown_versions(self) -> None:
        valid = (
            '{"event_id":"3d5157f1-701f-4e4f-a817-73b3944a5c35",'
            '"event_type":"ticket.closed","event_version":1,'
            '"occurred_at":"2026-08-04T10:00:00Z","tenant_id":"tenant_demo",'
            '"request_id":"req_demo_001","trace_id":"trace_demo_001",'
            '"payload":{"ticket_id":"ticket_1"}}'
        )
        event = parse_supported_event(valid)
        self.assertEqual(event.event_type, "ticket.closed")
        self.assertEqual(event.event_version, 1)

        with self.assertRaises(InvalidEvent):
            parse_supported_event(valid.replace("tenant_demo", ""))
        with self.assertRaises(UnsupportedEventVersion):
            parse_supported_event(
                valid.replace('"event_version":1', '"event_version":999')
            )

    async def test_outbox_reclaim_fences_old_worker_and_reaches_dlq(self) -> None:
        outbox = InMemoryOutbox()
        event = outbox.add()
        now = datetime(2026, 1, 1, tzinfo=UTC)
        first = outbox.claim("worker-a", now, lease_seconds=1)
        self.assertIsNotNone(first)
        old_token = first.lease_token
        reclaimed = outbox.claim("worker-b", now + timedelta(seconds=2))
        self.assertEqual(reclaimed.id, event.id)
        self.assertFalse(outbox.mark_published(event.id, "worker-a", old_token))
        self.assertTrue(
            outbox.mark_failed(
                event.id,
                "worker-b",
                reclaimed.lease_token,
                now + timedelta(seconds=2),
                "down",
                max_attempts=1,
            )
        )
        self.assertEqual(event.state, OutboxState.DEAD)

    async def test_fake_rag_filters_tenant_and_limits_sources(self) -> None:
        answer = answer_with_fake_rag(
            [
                Document("a", "tenant_a", "reset password"),
                Document("secret-b", "tenant_b", "reset password"),
            ],
            tenant_id="tenant_a",
            query="reset password",
            max_sources=1,
        )
        self.assertEqual(answer.source_ids, ("a",))


if __name__ == "__main__":
    unittest.main()
