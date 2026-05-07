import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-slim-classify-smoke-report.json"
)


def test_onnx_musicnn_optional_slim_classify_smoke_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.93"
    assert report["optional_slim_classify_smoke"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False

    service = report["service"]
    assert service["name"] == "genre-classifier-onnx"
    assert service["profile"] == "onnx"
    assert service["target"] == "onnx-runtime-slim"
    assert service["provider"] == "onnx_musicnn"

    docker = report["docker"]
    assert docker["compose_up_run"] is True
    assert docker["default_service_started"] is False
    assert docker["service_stopped_after_smoke"] is True

    health = report["health"]
    assert health["called"] is True
    assert health["ok"] is True
    assert health["status_code"] == 200

    smoke = report["classify_smoke"]
    assert smoke["called"] is True
    assert smoke["status_code"] == 200
    assert smoke["json_parse_ok"] is True
    assert smoke["ok"] is True
    assert smoke["required_fields_present"] is True
    assert smoke["response_shape"] == ["ok", "message", "genres", "genres_pretty"]
    assert smoke["genres_non_empty"] is True
    assert smoke["genres_pretty_non_empty"] is True
    assert isinstance(smoke["genres"], list)
    assert isinstance(smoke["genres_pretty"], list)
    assert smoke["genres"]
    assert smoke["genres_pretty"]

    artifacts = report["artifacts"]
    assert artifacts["persistent_mount_used"] is True
    assert artifacts["model_checksum_match"] is True
    assert artifacts["metadata_checksum_match"] is True

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == []
