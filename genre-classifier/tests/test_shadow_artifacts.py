import json

from app.services.shadow_artifacts import (
    SHADOW_EVIDENCE_SCHEMA_VERSION,
    append_shadow_evidence_jsonl,
    build_shadow_evidence_payload,
)
from app.services.shadow_compare import compare_shadow_tags
from app.services.runtime_shadow import ShadowRunOutcome


def test_build_shadow_evidence_payload_success_outcome():
    comparison = compare_shadow_tags(["rock"], ["rock"])
    outcome = ShadowRunOutcome(
        status="success",
        comparison=comparison,
        shadow_tags=["rock"],
        duration_ms=12.5,
    )

    payload = build_shadow_evidence_payload(
        request_id="request-1",
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=["rock"],
        outcome=outcome,
        input_fingerprint="sha256:test",
        timestamp_utc="2026-04-27T00:00:00+00:00",
    )

    assert payload["schema_version"] == SHADOW_EVIDENCE_SCHEMA_VERSION
    assert payload["providers"]["production"] == "legacy_musicnn"
    assert payload["providers"]["shadow"] == "llm"
    assert payload["legacy"]["tags"] == ["rock"]
    assert payload["shadow"]["status"] == "success"
    assert payload["shadow"]["tags"] == ["rock"]
    assert payload["comparison"]["shared_tags"] == ["rock"]
    assert payload["comparison"]["comparison_signal"] == "exact_match"


def test_build_shadow_evidence_payload_skipped_or_timeout_without_comparison():
    outcome = ShadowRunOutcome(
        status="timeout",
        comparison=None,
        shadow_tags=[],
        duration_ms=2.0,
        error_type=None,
        error_message=None,
    )

    payload = build_shadow_evidence_payload(
        request_id="request-1",
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=["rock"],
        outcome=outcome,
    )

    assert payload["shadow"]["status"] == "timeout"
    assert payload["comparison"] is None


def test_build_shadow_evidence_payload_allows_missing_request_and_fingerprint():
    outcome = ShadowRunOutcome(
        status="skipped_by_config",
        comparison=None,
        shadow_tags=[],
        duration_ms=0.0,
    )

    payload = build_shadow_evidence_payload(
        request_id=None,
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=[],
        outcome=outcome,
        input_fingerprint=None,
    )

    assert payload["request_id"] is None
    assert payload["input"]["input_fingerprint"] is None
    json.dumps(payload)


def test_build_shadow_evidence_payload_preserves_timestamp_override():
    outcome = ShadowRunOutcome(
        status="skipped_by_sampling",
        comparison=None,
        shadow_tags=[],
        duration_ms=0.0,
    )

    payload = build_shadow_evidence_payload(
        request_id=None,
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=[],
        outcome=outcome,
        timestamp_utc="2026-04-27T12:00:00+00:00",
    )

    assert payload["timestamp_utc"] == "2026-04-27T12:00:00+00:00"


def test_build_shadow_evidence_payload_is_json_serializable():
    comparison = compare_shadow_tags(["rock", "alternative"], ["rock", "indie"])
    outcome = ShadowRunOutcome(
        status="success",
        comparison=comparison,
        shadow_tags=["rock", "indie"],
        duration_ms=1.25,
    )

    payload = build_shadow_evidence_payload(
        request_id="request-1",
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=["rock", "alternative"],
        outcome=outcome,
    )

    json.dumps(payload)


def test_append_shadow_evidence_jsonl_success(tmp_path):
    payload = _build_minimal_payload()
    artifact_path = tmp_path / "runtime_shadow.jsonl"

    result = append_shadow_evidence_jsonl(payload, artifact_path=artifact_path)

    assert result.success is True
    assert result.path == str(artifact_path)
    lines = artifact_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    written_payload = json.loads(lines[0])
    assert written_payload["schema_version"] == SHADOW_EVIDENCE_SCHEMA_VERSION


def test_append_shadow_evidence_jsonl_appends(tmp_path):
    first_payload = _build_minimal_payload(request_id="first")
    second_payload = _build_minimal_payload(request_id="second")
    artifact_path = tmp_path / "runtime_shadow.jsonl"

    first_result = append_shadow_evidence_jsonl(first_payload, artifact_path=artifact_path)
    second_result = append_shadow_evidence_jsonl(second_payload, artifact_path=artifact_path)

    assert first_result.success is True
    assert second_result.success is True
    lines = artifact_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["request_id"] == "first"
    assert json.loads(lines[1])["request_id"] == "second"


def test_append_shadow_evidence_jsonl_creates_parent_directory(tmp_path):
    payload = _build_minimal_payload()
    artifact_path = tmp_path / "a" / "b" / "runtime_shadow.jsonl"

    result = append_shadow_evidence_jsonl(payload, artifact_path=artifact_path)

    assert result.success is True
    assert artifact_path.exists()


def test_append_shadow_evidence_jsonl_reports_non_serializable_payload_failure(tmp_path):
    artifact_path = tmp_path / "runtime_shadow.jsonl"

    result = append_shadow_evidence_jsonl(
        {"schema_version": object()},
        artifact_path=artifact_path,
    )

    assert result.success is False
    assert result.path == str(artifact_path)
    assert result.error_type == "TypeError"


def test_append_shadow_evidence_jsonl_reports_io_failure(tmp_path):
    payload = _build_minimal_payload()
    artifact_path = tmp_path / "runtime_shadow_directory"
    artifact_path.mkdir()

    result = append_shadow_evidence_jsonl(payload, artifact_path=artifact_path)

    assert result.success is False
    assert result.path == str(artifact_path)
    assert result.error_type in ("IsADirectoryError", "OSError")


def test_shadow_artifact_helpers_do_not_require_runtime_or_provider_factory(tmp_path):
    payload = _build_minimal_payload()

    result = append_shadow_evidence_jsonl(
        payload,
        artifacts_dir=tmp_path,
        filename="runtime_shadow.jsonl",
    )

    assert result.success is True


def _build_minimal_payload(request_id="request-1"):
    outcome = ShadowRunOutcome(
        status="success",
        comparison=compare_shadow_tags(["rock"], ["rock"]),
        shadow_tags=["rock"],
        duration_ms=1.0,
    )
    return build_shadow_evidence_payload(
        request_id=request_id,
        production_provider="legacy_musicnn",
        shadow_provider="llm",
        legacy_tags=["rock"],
        outcome=outcome,
        input_fingerprint="sha256:test",
        timestamp_utc="2026-04-27T00:00:00+00:00",
    )
