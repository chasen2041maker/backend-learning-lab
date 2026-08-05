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
    per_call_timeout_seconds: float,
    total_timeout_seconds: float,
) -> dict[str, CallResult]:
    """Run independent I/O calls with concurrency, per-call and total bounds."""
    if (
        max_concurrency < 1
        or per_call_timeout_seconds <= 0
        or total_timeout_seconds <= 0
    ):
        raise ValueError("limits must be positive")
    semaphore = asyncio.Semaphore(max_concurrency)
    deadline = asyncio.get_running_loop().time() + total_timeout_seconds
    deadline_expired = asyncio.Event()

    async def run_one(
        name: str, call: Callable[[], Awaitable[str]]
    ) -> tuple[str, CallResult]:
        deadline_limited = False
        try:
            async with semaphore:
                if deadline_expired.is_set():
                    return name, CallResult(value=None, error="deadline_exceeded")
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    deadline_expired.set()
                    return name, CallResult(value=None, error="deadline_exceeded")
                deadline_limited = remaining <= per_call_timeout_seconds
                try:
                    value = await asyncio.wait_for(
                        call(), timeout=min(per_call_timeout_seconds, remaining)
                    )
                except TimeoutError:
                    if deadline_limited:
                        deadline_expired.set()
                    raise
            return name, CallResult(value=value, error=None)
        except TimeoutError:
            error = (
                "deadline_exceeded"
                if deadline_limited or asyncio.get_running_loop().time() >= deadline
                else "timeout"
            )
            return name, CallResult(value=None, error=error)
        except Exception as exc:  # noqa: BLE001 - this is the dependency boundary.
            return name, CallResult(value=None, error=type(exc).__name__)

    tasks = {
        name: asyncio.create_task(run_one(name, call)) for name, call in calls.items()
    }
    try:
        async with asyncio.timeout(total_timeout_seconds):
            results = await asyncio.gather(*tasks.values())
    except TimeoutError:
        for task in tasks.values():
            task.cancel()
        await asyncio.gather(*tasks.values(), return_exceptions=True)
        results_by_name: dict[str, CallResult] = {}
        for name, task in tasks.items():
            if task.done() and not task.cancelled():
                try:
                    _, result = task.result()
                except Exception:  # noqa: BLE001 - cancellation boundary.
                    result = CallResult(value=None, error="deadline_exceeded")
                results_by_name[name] = result
            else:
                results_by_name[name] = CallResult(
                    value=None, error="deadline_exceeded"
                )
        return results_by_name
    return dict(results)
