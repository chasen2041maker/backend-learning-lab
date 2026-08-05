from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from stream_demo import DLQ_STREAM, GROUP, STREAM, process_entry


class FakeRedis:
    def __init__(self) -> None:
        self.markers: set[str] = set()
        self.acknowledged: list[tuple[str, str, str]] = []
        self.dead_letters: list[tuple[str, dict[str, str]]] = []

    async def exists(self, key: str) -> bool:
        return key in self.markers

    async def set(self, key: str, value: str, *, ex: int) -> None:
        self.markers.add(key)

    async def xack(self, stream: str, group: str, message_id: str) -> None:
        self.acknowledged.append((stream, group, message_id))

    async def xadd(self, stream: str, fields: dict[str, str]) -> str:
        self.dead_letters.append((stream, fields))
        return "dlq-1"


def valid_event(*, version: int = 1) -> str:
    return json.dumps(
        {
            "event_id": "3d5157f1-701f-4e4f-a817-73b3944a5c35",
            "event_type": "ticket.closed",
            "event_version": version,
            "occurred_at": "2026-08-04T10:00:00Z",
            "tenant_id": "tenant_demo",
            "request_id": "req_demo_001",
            "trace_id": "trace_demo_001",
            "payload": {
                "ticket_id": "00000000-0000-4000-8000-000000000001",
                "status": "closed",
                "version": 2,
            },
        }
    )


class StreamContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_event_is_processed_and_acked(self) -> None:
        redis = FakeRedis()
        await process_entry(
            redis,
            "message-1",
            {"event": valid_event()},
            ack=True,
        )
        self.assertEqual(redis.dead_letters, [])
        self.assertEqual(redis.acknowledged, [(STREAM, GROUP, "message-1")])

    async def test_invalid_event_is_dead_lettered_before_ack(self) -> None:
        redis = FakeRedis()
        await process_entry(
            redis,
            "message-2",
            {"event": '{"event_id":"not-a-uuid"}'},
            ack=True,
        )
        self.assertEqual(len(redis.dead_letters), 1)
        self.assertEqual(redis.dead_letters[0][0], DLQ_STREAM)
        self.assertEqual(redis.acknowledged, [(STREAM, GROUP, "message-2")])

    async def test_unknown_event_version_is_dead_lettered(self) -> None:
        redis = FakeRedis()
        await process_entry(
            redis,
            "message-3",
            {"event": valid_event(version=999)},
            ack=True,
        )
        self.assertEqual(len(redis.dead_letters), 1)
        self.assertIn("unsupported event version", redis.dead_letters[0][1]["reason"])
        self.assertEqual(redis.acknowledged, [(STREAM, GROUP, "message-3")])

    async def test_timestamp_without_timezone_is_dead_lettered(self) -> None:
        redis = FakeRedis()
        event = valid_event().replace("2026-08-04T10:00:00Z", "2026-08-04T10:00:00")
        await process_entry(redis, "message-4", {"event": event}, ack=True)
        self.assertEqual(len(redis.dead_letters), 1)
        self.assertIn("timezone", redis.dead_letters[0][1]["reason"])
        self.assertEqual(redis.acknowledged, [(STREAM, GROUP, "message-4")])

    async def test_invalid_ticket_closed_payload_is_dead_lettered_without_effect(
        self,
    ) -> None:
        invalid_payloads = (
            {"status": "closed", "version": 2},
            {"ticket_id": "not-a-uuid", "status": "closed", "version": 2},
            {
                "ticket_id": "00000000-0000-4000-8000-000000000001",
                "status": "open",
                "version": 2,
            },
            {
                "ticket_id": "00000000-0000-4000-8000-000000000001",
                "status": "closed",
                "version": "2",
            },
            {
                "ticket_id": "00000000-0000-4000-8000-000000000001",
                "status": "closed",
                "version": 0,
            },
            {
                "ticket_id": "00000000-0000-4000-8000-000000000001",
                "status": "closed",
                "version": 2,
                "secret": "unexpected",
            },
        )
        for index, payload in enumerate(invalid_payloads):
            with self.subTest(payload=payload):
                redis = FakeRedis()
                event = json.loads(valid_event())
                event["payload"] = payload
                message_id = f"invalid-{index}"
                await process_entry(
                    redis,
                    message_id,
                    {"event": json.dumps(event)},
                    ack=True,
                )
                self.assertEqual(redis.markers, set())
                self.assertEqual(len(redis.dead_letters), 1)
                self.assertEqual(redis.acknowledged, [(STREAM, GROUP, message_id)])


if __name__ == "__main__":
    unittest.main()
