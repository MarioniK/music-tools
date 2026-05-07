import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.101-onnx-candidate-integration-smoke.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-candidate-integration-smoke-report.json"
)


def test_onnx_candidate_integration_smoke_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.101"
    assert report["onnx_candidate_integration_smoke"] is True
    assert report["runtime_smoke_run"] is True
    assert report["default_switch"] is False
    assert report["production_tidal_parser_mutated"] is False
    assert report["production_genre_classifier_mutated"] is False
    assert report["docker_build_run"] is True
    assert report["docker_compose_up_run_for_onnx_candidate"] is True
    assert report["docker_compose_run_run"] is False
    assert report["one_off_tidal_parser_container_used"] is True
    assert report["parse_request_called"] is True
    assert report["network_http_called"] is True
    assert report["direct_classify_called"] is False

    baseline = report["current_stable_baseline"]
    assert baseline["genre_classifier_provider"] == "legacy_musicnn"
    assert baseline["genre_classifier_target"] == "legacy-runtime"
    assert baseline["onnx_is_default"] is False
    assert baseline["legacy_integration_smoke_passed"] is True

    candidate = report["onnx_candidate"]
    assert candidate["service"] == "genre-classifier-onnx"
    assert candidate["profile"] == "onnx"
    assert candidate["target"] == "onnx-runtime-slim"
    assert candidate["url_from_one_off_tidal_parser"] == "http://genre-classifier-onnx:8021/classify"
    assert candidate["health_status_code"] == 200
    assert candidate["provider_selected"] == "onnx_musicnn"

    request = report["request"]
    assert request["endpoint"] == "POST /"
    assert request["method"] == "POST"
    assert request["tidal_url"] == "https://tidal.com/track/498894205/u"
    assert request["audio_fixture"] == "/tmp/upload.mp3"
    assert request["http_status"] == 200
    assert request["content_type"] == "text/html; charset=utf-8"
    assert request["response_excerpt_recorded"] is True
    assert request["reference_id_error_present"] is False

    integration_result = report["integration_result"]
    assert integration_result["success"] is True
    assert integration_result["tidal_parser_successful_response"] is True
    assert integration_result["onnx_genre_classifier_file_processing_succeeded"] is True
    assert integration_result["onnx_provider_log_confirmed"] is True
    assert integration_result["response_shape_preserved"] is True
    assert integration_result["audio_classification_present"] is True
    assert integration_result["request_id"] == "8198daeb1d7a46a483b1e50bf0ba5ce6"
    assert integration_result["reference_id"] is None

    production_after_smoke = report["production_after_smoke"]
    assert production_after_smoke["legacy_tidal_parser_health_ok"] is True
    assert production_after_smoke["legacy_genre_classifier_health_ok"] is True
    assert production_after_smoke["legacy_default_unchanged"] is True
    assert production_after_smoke["onnx_candidate_stopped_after_smoke"] is True

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["app_code_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["tidal_parser_code_changed"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == []
