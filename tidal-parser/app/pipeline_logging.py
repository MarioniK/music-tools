import logging
from time import perf_counter
from typing import Awaitable, Callable, TypeVar

from app import request_context

logger = logging.getLogger("tidal_parser")


def _configure_library_loggers():
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_context.get_current_request_id()
        record.request_id = request_id

        message = record.getMessage()
        if "request_id=" not in message:
            record.msg = "request_id={} {}".format(request_id, message)
            record.args = ()

        return True


def _configure_app_logger():
    if not any(isinstance(existing_filter, RequestContextFilter) for existing_filter in logger.filters):
        logger.addFilter(RequestContextFilter())


if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

_configure_library_loggers()
_configure_app_logger()

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
