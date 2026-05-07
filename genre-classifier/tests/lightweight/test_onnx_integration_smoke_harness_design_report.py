import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.100-onnx-integration-smoke-harness-design.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-integration-smoke-harness-design-report.json"
)


def test_onnx_integration_smoke_harness_design_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.100"
    assert report["onnx_integration_smoke_harness_design"] is True
    assert report["documentation_only"] is True
    assert report["runtime_smoke_run"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["docker_compose_up_run"] is False
    assert report["classify_called"] is False
    assert report["parse_request_called"] is False
    assert report["network_http_called"] is False
    assert report["inference_run"] is False
    assert report["preprocessing_run"] is False

    baseline = report["current_stable_baseline"]
    assert baseline["genre_classifier_provider"] == "legacy_musicnn"
    assert baseline["genre_classifier_target"] == "legacy-runtime"
    assert baseline["onnx_is_default"] is False
    assert baseline["onnx_status"] == "candidate_not_default"
    assert baseline["legacy_integration_smoke_passed"] is True

    classifier_url = report["tidal_parser_classifier_url"]
    assert classifier_url["env_var"] == "AUDIO_CLASSIFIER_URL"
    assert classifier_url["default_value"] == "http://genre-classifier:8021/classify"
    assert classifier_url["source_file"] == "tidal-parser/app/settings.py"
    assert "runtime per classify request" in classifier_url["read_timing"]
    assert classifier_url["override_without_code_change_possible"] is True

    compose_findings = report["compose_findings"]
    assert compose_findings["tidal_parser_compose_present"] is True
    assert compose_findings["genre_classifier_default_service"] == "genre-classifier"
    assert compose_findings["genre_classifier_default_target"] == "legacy-runtime"
    assert compose_findings["onnx_candidate_service_present"] is True
    assert compose_findings["onnx_candidate_profile"] == "onnx"
    assert compose_findings["onnx_candidate_port_conflict_risk"] == "low"
    assert compose_findings["recommended_candidate_url"] == "http://genre-classifier-onnx:8021/classify"

    harness_options = report["harness_options"]
    assert [item["name"] for item in harness_options] == [
        "one_off_tidal_parser_with_classifier_url_override",
        "temporary_production_tidal_parser_env_override",
        "external_wrapper_smoke_harness",
    ]
    assert harness_options[0]["recommended"] is True
    assert harness_options[0]["production_mutation"] is False
    assert harness_options[0]["requires_code_change"] is False
    assert harness_options[1]["recommended"] is False
    assert harness_options[1]["production_mutation"] is True
    assert harness_options[1]["requires_code_change"] is False
    assert harness_options[2]["recommended"] is False
    assert harness_options[2]["production_mutation"] is False
    assert harness_options[2]["requires_code_change"] is False

    recommended_harness = report["recommended_harness"]
    assert recommended_harness["name"] == "one_off_tidal_parser_with_classifier_url_override"
    assert "env-driven override" in recommended_harness["reason"]
    assert recommended_harness["future_roadmap"] == "4.101"
    assert recommended_harness["requires_runtime_actions"] is True
    assert recommended_harness["requires_default_switch"] is False
    assert recommended_harness["requires_tidal_parser_code_change"] is False

    assert report["future_smoke_success_criteria"] == [
        "tidal-parser successful response using ONNX candidate classifier URL",
        "genre-classifier ONNX logs show provider_name=onnx_musicnn",
        "no user-facing Reference ID error",
        "response shape preserved",
        "production legacy baseline remains unchanged after smoke",
    ]

    assert report["guardrails"] == [
        "Do not switch default provider.",
        "Do not mutate production tidal-parser environment for the smoke unless explicitly approved.",
        "Do not remove legacy Essentia dependency.",
        "Do not commit ONNX artifacts.",
        "Do not combine harness implementation with default switch.",
    ]

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["app_code_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["tidal_parser_code_changed"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "This step is a design gate only; no smoke was executed.",
        "The recommended path assumes the smoke runner can start a one-off parser container on the shared musicnet network.",
    ]
