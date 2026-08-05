from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

from event_contract import InvalidEvent, UnsupportedEventVersion, parse_supported_event
from redis.asyncio import Redis
from redis.exceptions import ResponseError

STREAM = "lab:events"
DLQ_STREAM = "lab:events:dlq"
GROUP = "lab-consumers"
CONSUMER = "learner-1"
RECOVERY_CONSUMER = "learner-recovery"


async def ensure_group(redis: Redis) -> None:
    try:
        await redis.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def produce(redis: Redis) -> None:
    event_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "event_type": "ticket.closed",
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tenant_id": "tenant_demo",
        "request_id": f"req_{uuid4().hex}",
        "trace_id": uuid4().hex,
        "payload": {"ticket_id": "ticket_1", "version": 2},
    }
    message_id = await redis.xadd(STREAM, {"event": json.dumps(payload)})
    print(f"produced message_id={message_id} event_id={event_id}")


async def process_entry(
    redis: Redis,
    message_id: str,
    fields: dict[str, str],
    *,
    ack: bool,
) -> None:
    raw_event = fields.get("event", "")
    try:
        event = parse_supported_event(raw_event)
    except UnsupportedEventVersion as exc:
        await dead_letter(redis, message_id, raw_event, str(exc))
        return
    except InvalidEvent as exc:
        await dead_letter(redis, message_id, raw_event, str(exc))
        return

    idempotency_key = f"lab:processed:{GROUP}:{event.event_id}"
    already_processed = await redis.exists(idempotency_key)
    if already_processed:
        print(f"duplicate event {event.event_id}: skip business effect")
    else:
        print(f"apply demo effect for {event.event_id}")
        print(
            "production: commit business effect + processed_events in one PostgreSQL transaction"
        )
        # This Redis marker is only observable demo state, not production idempotency.
        await redis.set(idempotency_key, "1", ex=86_400)
    if ack:
        await redis.xack(STREAM, GROUP, message_id)
        print(f"acked message_id={message_id}")
    else:
        print(f"simulated crash before ACK; message_id={message_id} remains pending")


async def dead_letter(
    redis: Redis, message_id: str, raw_event: str, reason: str
) -> None:
    await redis.xadd(
        DLQ_STREAM,
        {"source_message_id": message_id, "reason": reason, "event": raw_event},
    )
    await redis.xack(STREAM, GROUP, message_id)
    print(f"dead-lettered message_id={message_id}: {reason}")


async def consume_once(redis: Redis, *, ack: bool = True) -> None:
    await ensure_group(redis)
    messages = await redis.xreadgroup(
        groupname=GROUP,
        consumername=CONSUMER,
        streams={STREAM: ">"},
        count=1,
        block=2_000,
    )
    if not messages:
        print("no new message")
        return

    _, entries = messages[0]
    message_id, fields = entries[0]
    await process_entry(redis, message_id, fields, ack=ack)


async def show_pending(redis: Redis) -> None:
    await ensure_group(redis)
    summary = await redis.xpending(STREAM, GROUP)
    print(json.dumps(summary, ensure_ascii=False, default=str, indent=2))
    entries = await redis.xpending_range(STREAM, GROUP, min="-", max="+", count=10)
    print(json.dumps(entries, ensure_ascii=False, default=str, indent=2))


async def reclaim(redis: Redis) -> None:
    await ensure_group(redis)
    result = await redis.xautoclaim(
        STREAM,
        GROUP,
        RECOVERY_CONSUMER,
        min_idle_time=0,
        start_id="0-0",
        count=10,
    )
    entries = result[1]
    if not entries:
        print("no pending message to reclaim")
        return
    for message_id, fields in entries:
        print(f"reclaimed message_id={message_id} as {RECOVERY_CONSUMER}")
        await process_entry(redis, message_id, fields, ack=True)


async def main() -> None:
    commands = {"produce", "consume", "consume-crash", "pending", "reclaim"}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(
            "usage: python stream_demo.py "
            "[produce|consume|consume-crash|pending|reclaim]"
        )
    redis = Redis.from_url("redis://127.0.0.1:6379/0", decode_responses=True)
    try:
        command = sys.argv[1]
        if command == "produce":
            await produce(redis)
        elif command == "consume":
            await consume_once(redis)
        elif command == "consume-crash":
            await consume_once(redis, ack=False)
        elif command == "pending":
            await show_pending(redis)
        else:
            await reclaim(redis)
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
