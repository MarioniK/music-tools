import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT / "docs/lightweight/roadmap-4.97-onnx-default-switch-rollback-incident.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-default-switch-rollback-incident-report.json"
)


def test_onnx_default_switch_rollback_incident_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.97"
    assert report["onnx_default_switch_rollback_incident_record"] is True
    assert report["documentation_only"] is True
    assert report["runtime_smoke_run"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["inference_run"] is False
    assert report["preprocessing_run"] is False
    assert report["roadmap_4_96_report_removed_by_revert"] is True

    incident = report["incident"]
    assert incident["default_switch_commit"] == "7b94fec279154daaee354ed950c93fd899c28a4b"
    assert incident["rollback_commit"] == "70e24e0"
    assert incident["legacy_dependency_hotfix_commit"] == "4188c28"
    assert incident["symptom"] == "real tidal-parser flow failed after ONNX default switch"
    assert incident["user_visible_error_reference_id"] == "5364a1fe1e05401c8a80efdb806b5c61"
    assert incident["rollback_reason"] == (
        "standalone genre-classifier smoke was insufficient; full tidal-parser -> genre-classifier flow was not validated before default switch"
    )

    recovery = report["recovery"]
    assert recovery["default_provider_restored"] == "legacy_musicnn"
    assert recovery["default_service_target_restored"] == "legacy-runtime"
    assert recovery["requirements_txt_restored_legacy_essentia"] is True
    assert recovery["legacy_dependency"] == "essentia-tensorflow==2.1b6.dev1389"
    assert recovery["health_restored"] is True
    assert recovery["classify_restored"] is True
    assert recovery["real_parser_flow_restored"] is True
    assert recovery["onnx_leftover_image_removed"] is True
    assert recovery["build_cache_cleaned"] is True

    findings = report["root_causes_and_findings"]
    assert findings["primary_finding"] == (
        "ONNX default switch was premature because full parser integration smoke was missing."
    )
    assert findings["secondary_finding"] == (
        "Legacy rebuild was not reproducible after dependency isolation removed essentia from production requirements."
    )
    assert findings["legacy_startup_failure"] == "ModuleNotFoundError: No module named 'essentia'"
    assert findings["legacy_import_path"] == (
        "from essentia.standard import MonoLoader, TensorflowPredictMusiCNN"
    )
    assert findings["onnx_candidate_evidence_still_valid"] is True
    assert findings["onnx_default_approved"] is False

    baseline = report["current_stable_baseline"]
    assert baseline["provider"] == "legacy_musicnn"
    assert baseline["service_target"] == "legacy-runtime"
    assert baseline["requirements_txt_contains_essentia_tensorflow"] is True
    assert baseline["tidal_parser_touched"] is False
    assert baseline["artifacts_committed"] is False

    assert report["guardrails_before_next_default_switch_attempt"] == [
        "Run full tidal-parser -> genre-classifier integration smoke before default switch.",
        "Validate real parser-flow, not only standalone /classify.",
        "Keep rollback path ready and documented.",
        "Do not remove legacy runtime dependency while legacy remains fallback/default.",
        "Treat ONNX as candidate until integration smoke passes.",
    ]
    assert report["next_steps"] == [
        "Do not continue previous 4.97 WIP alignment as-is.",
        "Use a new integration-focused roadmap slice before any future ONNX default switch.",
        "Consider adding a reproducible test or operator smoke for tidal-parser -> genre-classifier boundary.",
        "Keep ONNX artifacts external and do not commit model files.",
    ]

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["app_code_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["requirements_changed"] is False
    assert production_boundaries["default_provider_changed_in_this_step"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "This record documents rollback and recovery; it does not re-approve ONNX as default."
    ]
