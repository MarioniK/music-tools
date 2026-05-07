import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT / "docs/lightweight/roadmap-4.105-lightweight-evidence-cleanup-plan.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "lightweight-evidence-cleanup-plan-report.json"
)


def test_lightweight_evidence_cleanup_plan_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.105"
    assert report["lightweight_evidence_cleanup_plan"] is True
    assert report["documentation_inventory_only"] is True
    assert report["files_deleted"] is False
    assert report["files_moved"] is False
    assert report["runtime_smoke_run"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["docker_compose_up_run"] is False
    assert report["classify_called"] is False
    assert report["parse_request_called"] is False
    assert report["network_http_called"] is False
    assert report["inference_run"] is False
    assert report["preprocessing_run"] is False

    current_release_anchor = report["current_release_anchor"]
    assert current_release_anchor["version"] == "v0.5.0"
    assert current_release_anchor["docs_exist"] is True
    assert current_release_anchor["onnx_runtime_doc_exists"] is True
    assert current_release_anchor["changelog_exists"] is True
    assert current_release_anchor["tag_created"] is False

    inventory = report["inventory"]
    assert inventory["lightweight_roadmap_docs_count"] == 95
    assert inventory["parity_scaffold_json_count"] == 56
    assert inventory["lightweight_report_tests_count"] == 22
    assert inventory["docs_lightweight_size"] == "1.6M"
    assert inventory["tests_lightweight_size"] == "1.7M"

    keep = report["keep"]
    assert keep["permanent_docs"] == [
        "README.md",
        "CHANGELOG.md",
        "genre-classifier/docs/onnx-runtime.md",
        "genre-classifier/docs/releases/v0.5.0.md",
    ]
    assert keep["runtime_tests_to_keep"] == [
        "genre-classifier/tests/test_settings.py",
        "genre-classifier/tests/test_provider_factory.py",
        "genre-classifier/tests/test_classify_orchestration.py",
        "genre-classifier/tests/lightweight/test_optional_onnx_dependency_packaging.py",
    ]
    assert keep["artifacts_to_keep"] == [
        "genre-classifier/app/models/msd-musicnn-1.pb",
    ]

    cleanup_candidates = report["cleanup_candidates"]
    assert cleanup_candidates["roadmap_docs"] == [
        "genre-classifier/docs/lightweight/roadmap-4.1-lightweight-classifier-research.md",
        "genre-classifier/docs/lightweight/roadmap-4.100-onnx-integration-smoke-harness-design.md",
        "genre-classifier/docs/lightweight/roadmap-4.99-legacy-integration-smoke.md",
    ]
    assert cleanup_candidates["parity_scaffold_reports"] == [
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/example-musicnn-onnx-parity-scaffold-dry-run-output.json",
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/legacy-integration-smoke-report.json",
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-provider-direct-smoke-report.json",
    ]
    assert cleanup_candidates["report_structure_tests"] == [
        "genre-classifier/tests/lightweight/test_legacy_integration_smoke_report.py",
        "genre-classifier/tests/lightweight/test_onnx_default_switch_readiness_gate_report.py",
        "genre-classifier/tests/lightweight/test_v050_onnx_release_documentation_consolidation_report.py",
    ]

    assert report["defer_until_after_tag"] == [
        "genre-classifier/docs/lightweight/roadmap-4.97-onnx-default-switch-rollback-incident.md",
        "genre-classifier/docs/lightweight/roadmap-4.103-controlled-onnx-default-switch.md",
        "genre-classifier/docs/lightweight/roadmap-4.104-v0.5.0-onnx-release-documentation-consolidation.md",
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-default-switch-rollback-incident-report.json",
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/controlled-onnx-default-switch-report.json",
        "genre-classifier/docs/lightweight/evaluation/parity-scaffold/v0.5.0-onnx-release-documentation-consolidation-report.json",
        "genre-classifier/tests/lightweight/test_onnx_default_switch_rollback_incident_report.py",
        "genre-classifier/tests/lightweight/test_controlled_onnx_default_switch_report.py",
        "genre-classifier/tests/lightweight/test_v050_onnx_release_documentation_consolidation_report.py",
    ]

    recommended_cleanup_strategy = report["recommended_cleanup_strategy"]
    assert recommended_cleanup_strategy["rewrite_git_history"] is False
    assert recommended_cleanup_strategy["delete_in_this_step"] is False
    assert recommended_cleanup_strategy["next_cleanup_step"] == "4.106"
    assert (
        recommended_cleanup_strategy["approach"]
        == "delete obsolete lightweight evidence only after v0.5.0 release docs are accepted and the tag is in place"
    )

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
        "This step only inventories cleanup candidates; no files are removed.",
    ]
