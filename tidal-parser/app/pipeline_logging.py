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


async def run_timed_stage(stage: str, coro: Awaitable[T]) -> T:
    t0 = perf_counter()
    logger.info("event=stage_start stage=%s", stage)
    try:
        result = await coro
    except Exception:
        logger.exception(
            "event=stage_error stage=%s duration_s=%.3f",
            stage,
            perf_counter() - t0,
        )
        raise
    logger.info(
        "event=stage_end stage=%s duration_s=%.3f",
        stage,
        perf_counter() - t0,
    )
    return result


def run_timed_stage_sync(stage: str, fn: Callable[[], T]) -> T:
    t0 = perf_counter()
    logger.info("event=stage_start stage=%s", stage)
    try:
        result = fn()
    except Exception:
        logger.exception(
            "event=stage_error stage=%s duration_s=%.3f",
            stage,
            perf_counter() - t0,
        )
        raise
    logger.info(
        "event=stage_end stage=%s duration_s=%.3f",
        stage,
        perf_counter() - t0,
    )
    return result
