import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = SERVICE_ROOT / "docs/lightweight/roadmap-4.99-legacy-integration-smoke.md"
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/legacy-integration-smoke-report.json"
)


def test_legacy_integration_smoke_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.99"
    assert report["legacy_integration_smoke"] is True
    assert report["runtime_smoke_run"] is True
    assert report["onnx_smoke_run"] is False
    assert report["default_switch"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_up_run"] is False
    assert report["docker_compose_run_run"] is False
    assert report["classify_called_directly"] is False
    assert report["parse_request_called"] is True
    assert report["network_http_called"] is True

    baseline = report["current_stable_baseline"]
    assert baseline["genre_classifier_provider"] == "legacy_musicnn"
    assert baseline["genre_classifier_target"] == "legacy-runtime"
    assert baseline["onnx_is_default"] is False
    assert baseline["onnx_status"] == "candidate_not_default"
    assert baseline["requirements_txt_contains_essentia_tensorflow"] is True

    services = report["services"]
    assert services["tidal_parser_container_running"] is True
    assert services["genre_classifier_container_running"] is True
    assert services["tidal_parser_health_ok"] is True
    assert services["genre_classifier_health_ok"] is True

    request = report["request"]
    assert request["endpoint"] == "POST /"
    assert request["method"] == "POST"
    assert request["tidal_url_redacted_or_recorded"] == "https://tidal.com/track/498894205/u"
    assert request["http_status"] == 200
    assert request["content_type"] == "text/html; charset=utf-8"
    assert request["response_excerpt_recorded"] is True
    assert request["reference_id_error_present"] is False

    integration_result = report["integration_result"]
    assert integration_result["success"] is True
    assert integration_result["tidal_parser_successful_response"] is True
    assert integration_result["genre_classifier_file_processing_succeeded"] is True
    assert integration_result["response_shape_preserved"] is True
    assert integration_result["audio_classification_present"] is True
    assert integration_result["graceful_degradation_documented"] is False
    assert isinstance(integration_result["request_id"], str)
    assert len(integration_result["request_id"]) == 32
    assert integration_result["reference_id"] is None

    log_evidence = report["log_evidence"]
    assert log_evidence["tidal_parser_logs_collected"] is True
    assert log_evidence["genre_classifier_logs_collected"] is True
    assert log_evidence["provider_selected"] == "legacy_musicnn"
    assert log_evidence["module_not_found_essentia"] is False
    assert log_evidence["server_5xx_seen"] is False

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["app_code_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_code_changed"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "provider_selected зафиксирован как legacy_musicnn по текущему stable baseline; в логах classifier не печатается explicit provider_name"
    ]
