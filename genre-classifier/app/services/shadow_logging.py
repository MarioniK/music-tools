from typing import Any, Dict, Optional

from app.services.shadow_artifacts import ShadowArtifactWriteResult
from app.services.runtime_shadow import ShadowRunOutcome


SHADOW_LOG_EVENT_SKIPPED = "genre_classifier.shadow.skipped"
SHADOW_LOG_EVENT_STARTED = "genre_classifier.shadow.started"
SHADOW_LOG_EVENT_COMPLETED = "genre_classifier.shadow.completed"
SHADOW_LOG_EVENT_FAILED = "genre_classifier.shadow.failed"
SHADOW_LOG_EVENT_TIMEOUT = "genre_classifier.shadow.timeout"
SHADOW_LOG_EVENT_COMPARISON_RECORDED = "genre_classifier.shadow.comparison_recorded"
SHADOW_LOG_EVENT_ARTIFACT_WRITE_FAILED = "genre_classifier.shadow.artifact_write_failed"
SHADOW_LOG_ERROR_MESSAGE_LIMIT = 300


def build_shadow_log_payload(
    *,
    event: str,
    status: Optional[str] = None,
    request_id: Optional[str] = None,
    production_provider: str = "legacy_musicnn",
    shadow_provider: str = "llm",
    shadow_enabled: Optional[bool] = None,
    shadow_sample_rate: Optional[float] = None,
    shadow_selected: Optional[bool] = None,
    legacy_tags_count: Optional[int] = None,
    outcome: Optional[ShadowRunOutcome] = None,
    artifact_write_result: Optional[ShadowArtifactWriteResult] = None,
) -> Dict[str, Any]:
    """Build a safe structured runtime shadow log payload without writing logs."""
    payload = {
        "event": event,
        "status": status,
        "request_id": request_id,
        "production_provider": production_provider,
        "shadow_provider": shadow_provider,
        "shadow_enabled": shadow_enabled,
        "shadow_sample_rate": shadow_sample_rate,
        "shadow_selected": shadow_selected,
        "legacy_tags_count": legacy_tags_count,
    }

    if outcome is not None:
        comparison = outcome.comparison
        comparison_legacy_tags_count = _read_comparison_value(
            comparison,
            "legacy_tag_count",
        )
        comparison_shadow_tags_count = _read_comparison_value(
            comparison,
            "llm_tag_count",
        )
        payload.update(
            {
                "status": outcome.status,
                "shadow_status": outcome.status,
                "duration_ms": outcome.duration_ms,
                "error_type": outcome.error_type,
                "error_message": _truncate_message(outcome.error_message),
                "legacy_tags_count": (
                    legacy_tags_count
                    if legacy_tags_count is not None
                    else comparison_legacy_tags_count
                ),
                "shadow_tags_count": (
                    comparison_shadow_tags_count
                    if comparison_shadow_tags_count is not None
                    else len(outcome.shadow_tags)
                ),
                "overlap_count": _read_comparison_value(
                    comparison,
                    "shared_tag_count",
                ),
                "missing_from_shadow_count": _count_comparison_tags(
                    comparison,
                    "legacy_only_tags",
                ),
                "extra_in_shadow_count": _count_comparison_tags(
                    comparison,
                    "llm_only_tags",
                ),
                "comparison_signal": _read_comparison_value(
                    comparison,
                    "comparison_signal",
                ),
                "shared_tag_count": _read_comparison_value(
                    comparison,
                    "shared_tag_count",
                ),
                "legacy_tag_count": _read_comparison_value(
                    comparison,
                    "legacy_tag_count",
                ),
                "llm_tag_count": _read_comparison_value(
                    comparison,
                    "llm_tag_count",
                ),
            }
        )

    if artifact_write_result is not None:
        payload.update(
            {
                "artifact_write_success": artifact_write_result.success,
                "artifact_path": (
                    None
                    if artifact_write_result.path is None
                    else str(artifact_write_result.path)
                ),
                "artifact_error_type": artifact_write_result.error_type,
                "artifact_error_message": _truncate_message(
                    artifact_write_result.error_message,
                ),
            }
        )

    return payload


def log_shadow_payload(logger, payload: Dict[str, Any]) -> None:
    """Emit one diagnostic shadow log record without allowing logging failures out."""
    try:
        logger.info(
            "event=%s status=%s",
            payload.get("event"),
            payload.get("status"),
            extra={"shadow_payload": payload},
        )
    except Exception:
        pass


def log_shadow_outcome(
    *,
    logger,
    outcome: ShadowRunOutcome,
    legacy_tags_count: Optional[int] = None,
    shadow_enabled: Optional[bool] = None,
    shadow_sample_rate: Optional[float] = None,
) -> None:
    payload = build_shadow_log_payload(
        event=classify_shadow_event_from_outcome(outcome),
        legacy_tags_count=legacy_tags_count,
        shadow_enabled=shadow_enabled,
        shadow_sample_rate=shadow_sample_rate,
        outcome=outcome,
    )
    log_shadow_payload(logger, payload)


def log_shadow_started(
    *,
    logger,
    legacy_tags_count: Optional[int] = None,
    shadow_enabled: Optional[bool] = None,
    shadow_sample_rate: Optional[float] = None,
) -> None:
    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_STARTED,
        status="started",
        legacy_tags_count=legacy_tags_count,
        shadow_enabled=shadow_enabled,
        shadow_sample_rate=shadow_sample_rate,
        shadow_selected=True,
    )
    log_shadow_payload(logger, payload)


def classify_shadow_event_from_outcome(outcome: ShadowRunOutcome) -> str:
    if outcome.status in (
        "skipped_by_config",
        "skipped_by_sampling",
        "skipped_by_concurrency",
    ):
        return SHADOW_LOG_EVENT_SKIPPED

    if outcome.status == "success":
        return SHADOW_LOG_EVENT_COMPLETED

    if outcome.status == "timeout":
        return SHADOW_LOG_EVENT_TIMEOUT

    if outcome.status in (
        "provider_error",
        "invalid_output",
        "comparison_error",
        "observer_error",
    ):
        return SHADOW_LOG_EVENT_FAILED

    return SHADOW_LOG_EVENT_FAILED


def _read_comparison_value(comparison, field_name: str):
    if comparison is None:
        return None

    if isinstance(comparison, dict):
        return comparison.get(field_name)

    return getattr(comparison, field_name, None)


def _count_comparison_tags(comparison, field_name: str):
    value = _read_comparison_value(comparison, field_name)
    if value is None:
        return None

    return len(value)


def _truncate_message(message: Optional[str]) -> Optional[str]:
    if message is None:
        return None

    return str(message)[:SHADOW_LOG_ERROR_MESSAGE_LIMIT]
