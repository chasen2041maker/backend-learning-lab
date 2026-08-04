from __future__ import annotations

import asyncio
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from authorization import ForbiddenError, Principal, ToolCall, authorize_tool_call
from concurrency_timeout import run_bounded
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
            timeout_seconds=0.05,
        )
        self.assertLessEqual(peak, 2)
        self.assertEqual(results["slow"].error, "timeout")

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
                event_id="evt_1",
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=1_001,
            )
        )
        self.assertFalse(
            verifier.verify_and_record(
                event_id="evt_1",
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=1_001,
            )
        )
        with self.assertRaises(InvalidWebhook):
            verifier.verify_and_record(
                event_id="evt_2",
                timestamp=1_000,
                raw_body=raw,
                supplied_signature=supplied,
                now=2_000,
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
