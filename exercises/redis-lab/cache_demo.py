from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass

from redis.asyncio import Redis


@dataclass(frozen=True)
class Ticket:
    id: str
    tenant_id: str
    title: str


FAKE_DATABASE = {
    ("tenant_demo", "ticket_1"): Ticket(
        id="ticket_1", tenant_id="tenant_demo", title="Cannot sign in"
    )
}
NOT_FOUND = "__not_found__"


async def get_ticket(redis: Redis, tenant_id: str, ticket_id: str) -> Ticket | None:
    key = f"lab:ticket:{tenant_id}:{ticket_id}"
    cached = await redis.get(key)
    if cached == NOT_FOUND:
        print("negative cache hit")
        return None
    if cached is not None:
        print("cache hit")
        return Ticket(**json.loads(cached))

    print("cache miss: read the fact source")
    ticket = FAKE_DATABASE.get((tenant_id, ticket_id))
    if ticket is None:
        await redis.set(key, NOT_FOUND, ex=10)
        return None
    await redis.set(key, json.dumps(asdict(ticket)), ex=60)
    return ticket


async def main() -> None:
    redis = Redis.from_url("redis://127.0.0.1:6379/0", decode_responses=True)
    try:
        await redis.delete("lab:ticket:tenant_demo:ticket_1")
        print(await get_ticket(redis, "tenant_demo", "ticket_1"))
        print(await get_ticket(redis, "tenant_demo", "ticket_1"))
        await redis.delete("lab:ticket:tenant_demo:ticket_1")
        print(await get_ticket(redis, "tenant_demo", "ticket_1"))
        print(await get_ticket(redis, "tenant_demo", "missing"))
        print(await get_ticket(redis, "tenant_demo", "missing"))
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
