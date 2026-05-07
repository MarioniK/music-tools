import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT / "docs/lightweight/roadmap-4.102-onnx-default-switch-readiness-gate.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-default-switch-readiness-gate-report.json"
)


def test_onnx_default_switch_readiness_gate_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.102"
    assert report["onnx_default_switch_readiness_gate"] is True
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

    current_default = report["current_default"]
    assert current_default["provider"] == "legacy_musicnn"
    assert current_default["target"] == "legacy-runtime"
    assert current_default["onnx_is_default"] is False

    evidence = report["evidence"]
    legacy = evidence["legacy_integration_smoke_4_99"]
    assert legacy["passed"] is True
    assert legacy["provider"] == "legacy_musicnn"
    assert legacy["http_status"] == 200
    assert legacy["reference_id_error_present"] is False
    assert legacy["file_processing_succeeded"] is True
    assert legacy["response_contains_audio_genres"] is True

    onnx = evidence["onnx_candidate_integration_smoke_4_101"]
    assert onnx["passed"] is True
    assert onnx["provider"] == "onnx_musicnn"
    assert onnx["http_status"] == 200
    assert onnx["reference_id_error_present"] is False
    assert onnx["file_processing_succeeded"] is True
    assert onnx["provider_log_confirmed"] is True
    assert onnx["production_mutated"] is False
    assert onnx["default_switch"] is False

    gap_closure = report["gap_closure"]
    assert gap_closure["standalone_classify_was_insufficient"] is True
    assert gap_closure["full_integration_smoke_now_completed_for_legacy"] is True
    assert gap_closure["full_integration_smoke_now_completed_for_onnx_candidate"] is True
    assert gap_closure["integration_gap_from_4_97_closed_for_tested_request"] is True

    readiness_decision = report["readiness_decision"]
    assert readiness_decision[
        "onnx_candidate_eligible_for_future_controlled_default_switch"
    ] is True
    assert readiness_decision["default_switch_approved_in_this_step"] is False
    assert readiness_decision["production_default_changed_in_this_step"] is False
    assert readiness_decision["requires_separate_switch_step"] is True
    assert readiness_decision["requires_immediate_post_switch_integration_smoke"] is True
    assert readiness_decision["legacy_rollback_must_remain"] is True

    assert report["remaining_risks"] == [
        "Only one parser request/audio fixture has been tested.",
        "ONNX output drift remains expected and must stay documented.",
        "Default ONNX runtime requires external artifacts to remain provisioned.",
        "Legacy must remain available as rollback.",
        "Post-switch integration smoke is mandatory after any future switch.",
    ]

    recommended_next_step = report["recommended_next_step"]
    assert recommended_next_step["roadmap"] == "4.103"
    assert recommended_next_step["title"] == "controlled ONNX default switch execution"
    assert recommended_next_step["must_be_separate_step"] is True
    assert recommended_next_step["must_include_rollback_plan"] is True
    assert recommended_next_step["must_include_post_switch_integration_smoke"] is True

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
        "This readiness gate does not switch default runtime.",
        "Evidence is based on one tested parser request.",
    ]
