from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CallResult:
    value: str | None
    error: str | None


async def run_bounded(
    calls: dict[str, Callable[[], Awaitable[str]]],
    *,
    max_concurrency: int,
    timeout_seconds: float,
) -> dict[str, CallResult]:
    """Run independent I/O calls with both concurrency and time bounds."""
    if max_concurrency < 1 or timeout_seconds <= 0:
        raise ValueError("limits must be positive")
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_one(
        name: str, call: Callable[[], Awaitable[str]]
    ) -> tuple[str, CallResult]:
        try:
            async with semaphore:
                value = await asyncio.wait_for(call(), timeout=timeout_seconds)
            return name, CallResult(value=value, error=None)
        except TimeoutError:
            return name, CallResult(value=None, error="timeout")
        except Exception as exc:  # noqa: BLE001 - this is the dependency boundary.
            return name, CallResult(value=None, error=type(exc).__name__)

    results = await asyncio.gather(
        *(run_one(name, call) for name, call in calls.items())
    )
    return dict(results)
