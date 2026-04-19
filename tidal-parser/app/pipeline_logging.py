import logging
from time import perf_counter
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger("tidal_parser")

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

T = TypeVar("T")


def _duration_ms(t0: float) -> int:
    return int((perf_counter() - t0) * 1000)


async def run_timed_stage(stage: str, coro: Awaitable[T]) -> T:
    t0 = perf_counter()
    try:
        result = await coro
    except Exception:
        logger.exception(
            "event=stage outcome=error stage=%s duration_ms=%d",
            stage,
            _duration_ms(t0),
        )
        raise
    logger.info(
        "event=stage outcome=success stage=%s duration_ms=%d",
        stage,
        _duration_ms(t0),
    )
    return result


def run_timed_stage_sync(stage: str, fn: Callable[[], T]) -> T:
    t0 = perf_counter()
    try:
        result = fn()
    except Exception:
        logger.exception(
            "event=stage outcome=error stage=%s duration_ms=%d",
            stage,
            _duration_ms(t0),
        )
        raise
    logger.info(
        "event=stage outcome=success stage=%s duration_ms=%d",
        stage,
        _duration_ms(t0),
    )
    return result
