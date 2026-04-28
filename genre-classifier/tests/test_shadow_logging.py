import json
import logging

from app.services.shadow_artifacts import ShadowArtifactWriteResult
from app.services.shadow_compare import compare_shadow_tags
from app.services.shadow_logging import (
    SHADOW_LOG_ERROR_MESSAGE_LIMIT,
    SHADOW_LOG_EVENT_COMPLETED,
    SHADOW_LOG_EVENT_FAILED,
    SHADOW_LOG_EVENT_SKIPPED,
    SHADOW_LOG_EVENT_STARTED,
    SHADOW_LOG_EVENT_TIMEOUT,
    build_shadow_log_payload,
    classify_shadow_event_from_outcome,
    log_shadow_outcome,
)
from app.services.runtime_shadow import ShadowRunOutcome


def test_build_shadow_log_payload_basic_fields():
    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_STARTED,
        request_id="request-1",
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        shadow_enabled=True,
        shadow_sample_rate=0.25,
        shadow_selected=True,
    )

    assert payload["event"] == SHADOW_LOG_EVENT_STARTED
    assert payload["request_id"] == "request-1"
    assert payload["production_provider"] == "legacy_musicnn"
    assert payload["shadow_provider"] == "llm"
    assert payload["shadow_enabled"] is True
    assert payload["shadow_sample_rate"] == 0.25
    assert payload["shadow_selected"] is True


def test_build_shadow_log_payload_success_outcome_fields():
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock"], ["rock"]),
        shadow_tags=["rock"],
        duration_ms=12.5,
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_COMPLETED,
        outcome=outcome,
    )

    assert payload["shadow_status"] == "success"
    assert payload["status"] == "success"
    assert payload["duration_ms"] == 12.5
    assert payload["comparison_signal"] == "exact_match"
    assert payload["shared_tag_count"] == 1
    assert payload["legacy_tag_count"] == 1
    assert payload["llm_tag_count"] == 1
    assert payload["legacy_tags_count"] == 1
    assert payload["shadow_tags_count"] == 1
    assert payload["overlap_count"] == 1
    assert payload["missing_from_shadow_count"] == 0
    assert payload["extra_in_shadow_count"] == 0


def test_build_shadow_log_payload_outcome_without_comparison():
    outcome = ShadowRunOutcome(
        status="timeout",
        comparison=None,
        shadow_tags=[],
        duration_ms=2.0,
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_TIMEOUT,
        outcome=outcome,
    )

    assert payload["shadow_status"] == "timeout"
    assert payload["comparison_signal"] is None
    assert payload["shared_tag_count"] is None
    assert payload["legacy_tag_count"] is None
    assert payload["llm_tag_count"] is None


def test_classify_shadow_event_maps_timeout():
    outcome = ShadowRunOutcome(
        status="timeout",
        comparison=None,
        shadow_tags=[],
        duration_ms=1.0,
    )

    assert classify_shadow_event_from_outcome(outcome) == SHADOW_LOG_EVENT_TIMEOUT


def test_classify_shadow_event_maps_skipped_statuses():
    skipped_by_config = ShadowRunOutcome(
        status="skipped_by_config",
        comparison=None,
        shadow_tags=[],
        duration_ms=0.0,
    )
    skipped_by_sampling = ShadowRunOutcome(
        status="skipped_by_sampling",
        comparison=None,
        shadow_tags=[],
        duration_ms=0.0,
    )
    skipped_by_concurrency = ShadowRunOutcome(
        status="skipped_by_concurrency",
        comparison=None,
        shadow_tags=[],
        duration_ms=0.0,
    )

    assert classify_shadow_event_from_outcome(skipped_by_config) == SHADOW_LOG_EVENT_SKIPPED
    assert classify_shadow_event_from_outcome(skipped_by_sampling) == SHADOW_LOG_EVENT_SKIPPED
    assert classify_shadow_event_from_outcome(skipped_by_concurrency) == SHADOW_LOG_EVENT_SKIPPED


def test_classify_shadow_event_maps_failure_statuses():
    for status in ("provider_error", "invalid_output", "comparison_error", "observer_error"):
        outcome = ShadowRunOutcome(
            status=status,
            comparison=None,
            shadow_tags=[],
            duration_ms=1.0,
        )

        assert classify_shadow_event_from_outcome(outcome) == SHADOW_LOG_EVENT_FAILED


def test_classify_shadow_event_maps_success_to_completed():
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock"], ["rock"]),
        shadow_tags=["rock"],
        duration_ms=1.0,
    )

    assert classify_shadow_event_from_outcome(outcome) == SHADOW_LOG_EVENT_COMPLETED


def test_build_shadow_log_payload_artifact_write_success():
    artifact_result = ShadowArtifactWriteResult(
        success=True,
        path="/tmp/runtime_shadow.jsonl",
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_COMPLETED,
        artifact_write_result=artifact_result,
    )

    assert payload["artifact_write_success"] is True
    assert payload["artifact_path"] == "/tmp/runtime_shadow.jsonl"
    assert payload["artifact_error_type"] is None


def test_build_shadow_log_payload_artifact_write_failure():
    artifact_result = ShadowArtifactWriteResult(
        success=False,
        path="/tmp/runtime_shadow.jsonl",
        error_type="OSError",
        error_message="disk full",
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_FAILED,
        artifact_write_result=artifact_result,
    )

    assert payload["artifact_write_success"] is False
    assert payload["artifact_error_type"] == "OSError"
    assert payload["artifact_error_message"] == "disk full"


def test_build_shadow_log_payload_truncates_error_messages():
    long_message = "x" * (SHADOW_LOG_ERROR_MESSAGE_LIMIT + 50)
    outcome = ShadowRunOutcome(
        status="provider_error",
        comparison=None,
        shadow_tags=[],
        duration_ms=1.0,
        error_type="RuntimeError",
        error_message=long_message,
    )
    artifact_result = ShadowArtifactWriteResult(
        success=False,
        path="/tmp/runtime_shadow.jsonl",
        error_type="OSError",
        error_message=long_message,
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_FAILED,
        outcome=outcome,
        artifact_write_result=artifact_result,
    )

    assert len(payload["error_message"]) == SHADOW_LOG_ERROR_MESSAGE_LIMIT
    assert len(payload["artifact_error_message"]) == SHADOW_LOG_ERROR_MESSAGE_LIMIT


def test_build_shadow_log_payload_excludes_noisy_fields():
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock"], ["rock"]),
        shadow_tags=["rock"],
        duration_ms=1.0,
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_COMPLETED,
        outcome=outcome,
    )

    assert "raw_prompt" not in payload
    assert "raw_audio" not in payload
    assert "raw_llm_response" not in payload
    assert "source_url" not in payload
    assert "legacy_tags" not in payload
    assert "shadow_tags" not in payload
    assert "tags" not in payload
    assert "audio_path" not in payload
    assert "prompt" not in payload
    assert "response" not in payload


def test_log_shadow_outcome_emits_structured_payload(caplog):
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock", "pop"], ["rock", "indie"]),
        shadow_tags=["rock", "indie"],
        duration_ms=3.0,
    )
    logger = logging.getLogger("genre_classifier")

    with caplog.at_level(logging.INFO, logger="genre_classifier"):
        log_shadow_outcome(
            logger=logger,
            outcome=outcome,
            legacy_tags_count=2,
            shadow_enabled=True,
            shadow_sample_rate=1.0,
        )

    record = caplog.records[-1]
    payload = record.shadow_payload
    assert payload["event"] == SHADOW_LOG_EVENT_COMPLETED
    assert payload["status"] == "success"
    assert payload["legacy_tags_count"] == 2
    assert payload["shadow_tags_count"] == 2
    assert payload["overlap_count"] == 1
    assert payload["missing_from_shadow_count"] == 1
    assert payload["extra_in_shadow_count"] == 1


def test_log_shadow_outcome_swallows_logging_exceptions():
    class RaisingLogger:
        def info(self, *args, **kwargs):
            raise RuntimeError("logging failed")

    outcome = ShadowRunOutcome(
        status="provider_error",
        comparison=None,
        shadow_tags=[],
        duration_ms=1.0,
        error_type="RuntimeError",
    )

    log_shadow_outcome(logger=RaisingLogger(), outcome=outcome)


def test_build_shadow_log_payload_is_json_serializable():
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock", "alternative"], ["rock", "indie"]),
        shadow_tags=["rock", "indie"],
        duration_ms=1.0,
    )
    artifact_result = ShadowArtifactWriteResult(
        success=True,
        path="/tmp/runtime_shadow.jsonl",
    )

    payload = build_shadow_log_payload(
        event=SHADOW_LOG_EVENT_COMPLETED,
        request_id="request-1",
        shadow_enabled=True,
        shadow_sample_rate=0.5,
        shadow_selected=True,
        outcome=outcome,
        artifact_write_result=artifact_result,
    )

    json.dumps(payload)
