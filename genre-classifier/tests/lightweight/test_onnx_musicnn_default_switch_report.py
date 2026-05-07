import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-default-switch-report.json"
)


def test_onnx_musicnn_default_switch_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.96"
    assert report["onnx_default_switch"] is True
    assert report["production_readiness_granted_for_genre_classifier_default_runtime"] is True
    assert report["default_switch_approval"] is True
    assert report["default_provider_before"] == "legacy_musicnn"
    assert report["default_provider_after"] == "onnx_musicnn"
    assert report["default_service_target_before"] == "legacy-runtime"
    assert report["default_service_target_after"] == "onnx-runtime-slim"
    assert report["legacy_runtime_preserved"] is True
    assert report["legacy_provider_preserved"] is True
    assert report["rollback_path_documented"] is True

    artifacts = report["artifacts"]
    assert artifacts["external_host_path"] == "/opt/music-tools-artifacts/genre-classifier/onnx"
    assert artifacts["container_path"] == "/opt/genre-classifier/onnx"
    assert artifacts["model_checksum_match"] is True
    assert artifacts["metadata_checksum_match"] is True
    assert artifacts["artifacts_committed"] is False
    assert artifacts["artifacts_baked_into_image"] is False
    assert artifacts["runtime_downloads_by_default"] is False

    validation = report["validation"]
    assert validation["docker_compose_config_success"] is True
    assert validation["default_service_build_success"] is True
    assert validation["default_service_started"] is True
    assert validation["health_status_code"] == 200
    assert validation["classify_status_code"] == 200
    assert validation["classify_json_parse_ok"] is True
    assert validation["response_shape"] == ["ok", "message", "genres", "genres_pretty"]
    assert validation["response_shape_unchanged"] is True
    assert validation["genres_non_empty"] is True
    assert validation["genres_pretty_non_empty"] is True
    assert validation["provider_selected"] == "onnx_musicnn"

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["tidal_parser_touched"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["legacy_removed"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["known_changes"] == [
        "Default genre provider changes from legacy_musicnn to onnx_musicnn.",
        "Default Docker runtime target changes from legacy-runtime to onnx-runtime-slim.",
        "Default runtime now requires external ONNX artifacts to be provisioned.",
    ]
    assert report["known_risks"] == [
        "Output drift from legacy is expected and accepted.",
        "External artifact provisioning is now required for default runtime.",
        "Rollback requires switching provider/target back to legacy_musicnn/legacy-runtime.",
    ]
    assert report["blockers"] == []
    assert report["warnings"] == []
