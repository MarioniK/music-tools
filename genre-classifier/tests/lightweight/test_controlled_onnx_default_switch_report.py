import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.103-controlled-onnx-default-switch.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "controlled-onnx-default-switch-report.json"
)


def test_controlled_onnx_default_switch_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.103"
    assert report["controlled_onnx_default_switch"] is True
    assert report["switch_executed"] is True
    assert report["switch_success"] is True
    assert report["rollback_executed"] is False
    assert report["default_provider_before"] == "legacy_musicnn"
    assert report["default_provider_after"] == "onnx_musicnn"
    assert report["default_target_before"] == "legacy-runtime"
    assert report["default_target_after"] == "onnx-runtime-slim"
    assert report["legacy_provider_preserved"] is True
    assert report["legacy_runtime_preserved"] is True
    assert report["legacy_rollback_profile_present"] is True

    external_artifacts = report["external_artifacts"]
    assert external_artifacts["host_path"] == "/opt/music-tools-artifacts/genre-classifier/onnx"
    assert external_artifacts["container_path"] == "/opt/genre-classifier/onnx"
    assert external_artifacts["model_checksum_match"] is True
    assert external_artifacts["metadata_checksum_match"] is True
    assert external_artifacts["artifacts_committed"] is False

    validation = report["validation"]
    assert validation["compose_config_success"] is True
    assert validation["legacy_profile_config_success"] is True
    assert validation["default_service_build_success"] is True
    assert validation["default_service_recreated"] is True
    assert validation["genre_classifier_health_status"] == 200
    assert validation["tidal_parser_health_status"] == 200

    smoke = report["post_switch_integration_smoke"]
    assert smoke["run"] is True
    assert smoke["endpoint"] == "POST /"
    assert smoke["tidal_url"] == "https://tidal.com/track/498894205/u"
    assert smoke["http_status"] == 200
    assert smoke["content_type"] == "text/html; charset=utf-8"
    assert smoke["reference_id_error_present"] is False
    assert smoke["response_excerpt_recorded"] is True
    assert smoke["audio_classification_present"] is True
    assert smoke["tidal_parser_audio_classifier_success"] is True
    assert smoke["genre_classifier_file_processing_succeeded"] is True
    assert smoke["provider_log_confirmed"] is True
    assert smoke["provider_selected"] == "onnx_musicnn"

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["tidal_parser_code_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["legacy_removed"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "Evidence still uses one parser request/audio fixture.",
        "ONNX output drift remains expected and documented.",
        "Default runtime depends on external ONNX artifacts.",
        "Legacy rollback path must be kept.",
    ]
