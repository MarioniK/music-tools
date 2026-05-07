import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.98-tidal-parser-genre-classifier-integration-smoke-design.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "tidal-parser-genre-classifier-integration-smoke-design-report.json"
)


def test_tidal_parser_genre_classifier_integration_smoke_design_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.98"
    assert report["tidal_parser_genre_classifier_integration_smoke_design"] is True
    assert report["documentation_only"] is True
    assert report["runtime_smoke_run"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
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
    assert baseline["requirements_txt_contains_essentia_tensorflow"] is True

    design = report["design"]
    assert design["integration_path"] == "tidal-parser -> genre-classifier"
    assert design["legacy_baseline_smoke_next"] == "4.99"
    assert design["onnx_candidate_integration_smoke_later"] == "4.100"
    assert design["default_switch_blocked_until_integration_smoke_passes"] is True
    assert design["standalone_classify_smoke_considered_insufficient"] is True

    future_legacy_smoke = report["future_legacy_smoke"]
    assert future_legacy_smoke["roadmap"] == "4.99"
    assert future_legacy_smoke["purpose"] == "prove current stable parser-flow baseline"
    assert future_legacy_smoke["provider"] == "legacy_musicnn"
    assert future_legacy_smoke["default_switch"] is False
    assert future_legacy_smoke["success_criteria"] == [
        "tidal-parser successful response",
        "genre-classifier file_processing_succeeded",
        "no user-facing Reference ID error",
        "response shape preserved",
        "audio classification present or graceful degradation documented",
    ]

    future_onnx_candidate_smoke = report["future_onnx_candidate_smoke"]
    assert future_onnx_candidate_smoke["roadmap"] == "4.100"
    assert future_onnx_candidate_smoke["purpose"] == (
        "test ONNX candidate in full parser-flow without default switch"
    )
    assert future_onnx_candidate_smoke["provider"] == "onnx_musicnn"
    assert future_onnx_candidate_smoke["default_switch"] is False
    assert future_onnx_candidate_smoke["requires_explicit_classifier_url_or_profile_override"] is True
    assert future_onnx_candidate_smoke["success_criteria"] == [
        "tidal-parser successful response using ONNX candidate classifier endpoint",
        "genre-classifier logs show provider_name=onnx_musicnn",
        "no 5xx",
        "response shape preserved",
        "output drift accepted if controlled and documented",
    ]

    assert report["evidence_to_collect"] == [
        "command/request used",
        "HTTP status",
        "response shape/excerpt",
        "tidal-parser logs tail",
        "genre-classifier logs tail",
        "request_id or Reference ID",
        "provider selected",
        "duration if available",
    ]
    assert report["failure_handling"] == [
        "collect Reference ID on parser error",
        "collect genre-classifier traceback on classifier failure",
        "record timeout boundary",
        "treat response shape change as blocker",
        "keep legacy default if ONNX integration smoke fails",
    ]
    assert report["guardrails"] == [
        "No ONNX default switch before full integration smoke passes.",
        "Do not remove legacy Essentia dependency while legacy is default or fallback.",
        "Do not commit ONNX artifacts.",
        "Do not enable runtime downloads by default.",
        "Do not combine tidal-parser config migration with default switch.",
    ]

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["app_code_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "This step is a design gate only; no smoke was executed."
    ]
