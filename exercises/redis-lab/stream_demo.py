from __future__ import annotations

import asyncio
import json
import sys
from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import ResponseError

STREAM = "lab:events"
GROUP = "lab-consumers"
CONSUMER = "learner-1"


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
        "tenant_id": "tenant_demo",
        "payload": {"ticket_id": "ticket_1", "version": 2},
    }
    message_id = await redis.xadd(STREAM, {"event": json.dumps(payload)})
    print(f"produced message_id={message_id} event_id={event_id}")


async def consume_once(redis: Redis) -> None:
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
    event = json.loads(fields["event"])
    idempotency_key = f"lab:processed:{GROUP}:{event['event_id']}"
    already_processed = await redis.exists(idempotency_key)
    if already_processed:
        print(f"duplicate event {event['event_id']}: skip business effect")
    else:
        print(f"apply demo effect for {event['event_id']}")
        print("production: commit business effect + processed_events in one PostgreSQL transaction")
        # This Redis marker is only observable demo state, not production idempotency.
        await redis.set(idempotency_key, "1", ex=86_400)
    await redis.xack(STREAM, GROUP, message_id)
    print(f"acked message_id={message_id}")


async def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"produce", "consume"}:
        raise SystemExit("usage: python stream_demo.py [produce|consume]")
    redis = Redis.from_url("redis://127.0.0.1:6379/0", decode_responses=True)
    try:
        if sys.argv[1] == "produce":
            await produce(redis)
        else:
            await consume_once(redis)
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
