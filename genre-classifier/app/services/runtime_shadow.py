import asyncio
import logging
import random
import time
from dataclasses import dataclass
from threading import Lock
from typing import Awaitable, Callable, List, Optional, Sequence

from app.core import settings
from app.services.shadow_compare import (
    ShadowComparison,
    compare_shadow_tags,
    normalize_shadow_tags,
)


logger = logging.getLogger("genre_classifier")
_shadow_execution_lock = Lock()
_active_shadow_executions = 0


@dataclass(frozen=True)
class ShadowRunOutcome:
    status: str
    comparison: Optional[ShadowComparison]
    shadow_tags: List[str]
    duration_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None


async def run_configured_shadow_observer(
    *,
    legacy_tags: Sequence[str],
    shadow_runner: Callable[[], Awaitable[Sequence[str]]],
    random_value: Optional[float] = None,
) -> ShadowRunOutcome:
    """Apply runtime shadow execution guards before running the observer."""
    shadow_enabled = settings.get_configured_shadow_enabled()
    shadow_sample_rate = settings.get_configured_shadow_sample_rate()
    shadow_timeout_seconds = settings.get_configured_shadow_timeout_seconds()
    shadow_max_concurrent = settings.get_configured_shadow_max_concurrent()

    if not shadow_enabled:
        return _build_outcome(status="skipped_by_config")

    if shadow_sample_rate <= 0.0:
        return _build_outcome(status="skipped_by_sampling")

    if shadow_sample_rate < 1.0:
        selected_random_value = random.random() if random_value is None else random_value
        if selected_random_value >= shadow_sample_rate:
            return _build_outcome(status="skipped_by_sampling")

    if not _try_acquire_shadow_slot(shadow_max_concurrent):
        logger.debug(
            "event=shadow_execution_skipped reason=concurrency_saturated max_concurrent=%d",
            shadow_max_concurrent,
        )
        return _build_outcome(status="skipped_by_concurrency")

    started_at = time.monotonic()
    try:
        return await asyncio.wait_for(
            run_shadow_observer(
                legacy_tags=legacy_tags,
                shadow_runner=shadow_runner,
                shadow_enabled=True,
                shadow_sample_rate=1.0,
                shadow_timeout_seconds=shadow_timeout_seconds,
            ),
            timeout=shadow_timeout_seconds,
        )
    except asyncio.TimeoutError:
        return _build_outcome(
            status="timeout",
            duration_ms=_elapsed_ms(started_at),
        )
    except Exception as exc:
        return _build_error_outcome(
            status="observer_error",
            exc=exc,
            duration_ms=_elapsed_ms(started_at),
        )
    finally:
        _release_shadow_slot()


async def run_shadow_observer(
    *,
    legacy_tags: Sequence[str],
    shadow_runner: Callable[[], Awaitable[Sequence[str]]],
    shadow_enabled: bool,
    shadow_sample_rate: float,
    shadow_timeout_seconds: float,
    random_value: Optional[float] = None,
) -> ShadowRunOutcome:
    """Run an isolated diagnostic shadow observer without production side effects."""
    if not shadow_enabled:
        return _build_outcome(status="skipped_by_config")

    if shadow_sample_rate <= 0.0:
        return _build_outcome(status="skipped_by_sampling")

    if shadow_sample_rate < 1.0:
        selected_random_value = random.random() if random_value is None else random_value
        if selected_random_value >= shadow_sample_rate:
            return _build_outcome(status="skipped_by_sampling")

    started_at = time.monotonic()

    try:
        shadow_result = await asyncio.wait_for(
            shadow_runner(),
            timeout=shadow_timeout_seconds,
        )
    except asyncio.TimeoutError:
        return _build_outcome(
            status="timeout",
            duration_ms=_elapsed_ms(started_at),
        )
    except Exception as exc:
        return _build_error_outcome(
            status="provider_error",
            exc=exc,
            duration_ms=_elapsed_ms(started_at),
        )

    if not _is_valid_shadow_tags_result(shadow_result):
        return _build_outcome(
            status="invalid_output",
            duration_ms=_elapsed_ms(started_at),
            error_type=type(shadow_result).__name__,
            error_message="shadow runner returned invalid output",
        )

    shadow_tags = normalize_shadow_tags(shadow_result)

    try:
        comparison = compare_shadow_tags(legacy_tags, shadow_tags)
    except Exception as exc:
        return _build_error_outcome(
            status="comparison_error",
            exc=exc,
            duration_ms=_elapsed_ms(started_at),
        )

    return _build_outcome(
        status="success",
        comparison=comparison,
        shadow_tags=shadow_tags,
        duration_ms=_elapsed_ms(started_at),
    )


def _is_valid_shadow_tags_result(value) -> bool:
    if value is None or isinstance(value, (str, bytes, dict)):
        return False

    if not isinstance(value, Sequence):
        return False

    return all(isinstance(item, str) for item in value)


def _build_outcome(
    *,
    status: str,
    comparison: Optional[ShadowComparison] = None,
    shadow_tags: Optional[List[str]] = None,
    duration_ms: float = 0.0,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> ShadowRunOutcome:
    return ShadowRunOutcome(
        status=status,
        comparison=comparison,
        shadow_tags=shadow_tags or [],
        duration_ms=duration_ms,
        error_type=error_type,
        error_message=error_message,
    )


def _build_error_outcome(
    *,
    status: str,
    exc: Exception,
    duration_ms: float,
) -> ShadowRunOutcome:
    return _build_outcome(
        status=status,
        duration_ms=duration_ms,
        error_type=type(exc).__name__,
        error_message=_safe_error_message(exc),
    )


def _safe_error_message(exc: Exception) -> str:
    return str(exc)[:200]


def _elapsed_ms(started_at: float) -> float:
    return (time.monotonic() - started_at) * 1000.0


def _try_acquire_shadow_slot(max_concurrent: int) -> bool:
    global _active_shadow_executions

    with _shadow_execution_lock:
        if _active_shadow_executions >= max_concurrent:
            return False

        _active_shadow_executions += 1
        return True


def _release_shadow_slot():
    global _active_shadow_executions

    with _shadow_execution_lock:
        _active_shadow_executions = max(0, _active_shadow_executions - 1)
