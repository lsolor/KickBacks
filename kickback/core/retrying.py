from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    attempts: int = 3,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=2),
        retry=retry_if_exception_type(exceptions),
    ):
        with attempt:
            return await func()
    raise RuntimeError("Retry loop exhausted")  # pragma: no cover
