import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-slim-operational-readiness-gate-report.json"
)


def test_onnx_musicnn_slim_operational_readiness_gate_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.94"
    assert report["onnx_slim_operational_readiness_gate"] is True
    assert report["decision_type"] == "optional_runtime_candidate_promotion_gate"
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["default_switch_approval"] is False
    assert report["runtime_smoke_run"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False

    evidence = report["evidence"]

    slim_docker_target = evidence["slim_docker_target"]
    assert slim_docker_target["roadmap"] == "4.85"
    assert slim_docker_target["passed"] is True
    assert slim_docker_target["slim_image_size_bytes"] == 1572225060
    assert slim_docker_target["size_reduction_percent"] == 54.81
    assert slim_docker_target["tensorflow_python_package_absent"] is True

    slim_performance_baseline = evidence["slim_performance_baseline"]
    assert slim_performance_baseline["roadmap"] == "4.86"
    assert slim_performance_baseline["passed"] is True
    assert slim_performance_baseline["runtime_regression_detected"] is False
    assert slim_performance_baseline["performance_signal"] == "same/faster"

    compose_profile_static_validation = evidence["compose_profile_static_validation"]
    assert compose_profile_static_validation["roadmap"] == "4.87"
    assert compose_profile_static_validation["passed"] is True
    assert compose_profile_static_validation["optional_onnx_service_target"] == "onnx-runtime-slim"
    assert compose_profile_static_validation["default_service_target"] == "legacy-runtime"

    compose_config_and_artifact_path = evidence["compose_config_and_artifact_path"]
    assert compose_config_and_artifact_path["roadmap"] == "4.88"
    assert compose_config_and_artifact_path["passed"] is True
    assert compose_config_and_artifact_path["persistent_host_artifact_path"] == "/opt/music-tools-artifacts/genre-classifier/onnx"
    assert compose_config_and_artifact_path["artifacts_baked_into_image"] is False
    assert compose_config_and_artifact_path["runtime_downloads_by_default"] is False

    artifact_placement_checksum = evidence["artifact_placement_checksum"]
    assert artifact_placement_checksum["roadmap"] == "4.89"
    assert artifact_placement_checksum["passed"] is True
    assert artifact_placement_checksum["artifacts_outside_repo"] is True
    assert artifact_placement_checksum["model_checksum_match"] is True
    assert artifact_placement_checksum["metadata_checksum_match"] is True

    container_import_smoke = evidence["container_import_smoke"]
    assert container_import_smoke["roadmap"] == "4.90"
    assert container_import_smoke["passed"] is True
    assert container_import_smoke["tensorflow_absent"] is True
    assert container_import_smoke["tensorflow_input_musicnn_available"] is True
    assert container_import_smoke["provider_module_import_ok"] is True

    provider_direct_smoke = evidence["provider_direct_smoke"]
    assert provider_direct_smoke["roadmap"] == "4.91"
    assert provider_direct_smoke["passed"] is True
    assert provider_direct_smoke["patch_shape"] == [187, 96]
    assert provider_direct_smoke["activations_shape"] == [50]
    assert provider_direct_smoke["embeddings_shape"] == [200]
    assert provider_direct_smoke["genres_non_empty"] is True
    assert provider_direct_smoke["genres_pretty_non_empty"] is True

    legacy_vs_onnx_benchmark = evidence["legacy_vs_onnx_benchmark"]
    assert legacy_vs_onnx_benchmark["roadmap"] == "4.92"
    assert legacy_vs_onnx_benchmark["passed"] is True
    assert legacy_vs_onnx_benchmark["legacy_avg_total_seconds"] == 4.120633650318875
    assert legacy_vs_onnx_benchmark["onnx_slim_avg_total_seconds"] == 2.1574637469796776
    assert legacy_vs_onnx_benchmark["speedup_ratio_legacy_div_onnx"] == 1.9099434027976228
    assert legacy_vs_onnx_benchmark["memory_delta_kb"] == 335100
    assert legacy_vs_onnx_benchmark["performance_benefit_confirmed"] is True
    assert legacy_vs_onnx_benchmark["output_drift_documented"] is True

    optional_classify_smoke = evidence["optional_classify_smoke"]
    assert optional_classify_smoke["roadmap"] == "4.93"
    assert optional_classify_smoke["passed"] is True
    assert optional_classify_smoke["health_status_code"] == 200
    assert optional_classify_smoke["classify_status_code"] == 200
    assert optional_classify_smoke["response_shape"] == ["ok", "message", "genres", "genres_pretty"]
    assert optional_classify_smoke["provider_selected"] == "onnx_musicnn"

    promotion_decision = report["promotion_decision"]
    assert promotion_decision["documented_optional_runtime_candidate"] is True
    assert promotion_decision["preferred_optional_runtime_target"] == "onnx-runtime-slim"
    assert promotion_decision["default_provider_remains"] == "legacy_musicnn"
    assert promotion_decision["default_service_target_remains"] == "legacy-runtime"
    assert promotion_decision["onnx_provider_opt_in_only"] is True
    assert promotion_decision["production_readiness_granted"] is False
    assert promotion_decision["default_switch_allowed"] is False

    assert report["remaining_risks"] == [
        "ONNX artifacts require external provisioning outside repo.",
        "Output drift from legacy is controlled and documented but not identical.",
        "Smoke coverage currently uses limited fixture coverage.",
        "Production default switch requires broader validation and explicit approval.",
        "tidal-parser integration path has not been migrated or switched.",
    ]

    assert report["required_next_steps_before_production_readiness"] == [
        "Document operator artifact provisioning procedure.",
        "Add multi-fixture optional ONNX slim smoke or benchmark.",
        "Add optional runtime troubleshooting notes for missing artifacts/checksum mismatch.",
        "Decide whether to expose optional ONNX runtime in README/operator docs.",
        "Only after explicit approval, plan default switch separately.",
    ]

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False
    assert production_boundaries["artifacts_committed"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "This gate promotes ONNX slim only as a documented optional runtime candidate, not as production default."
    ]
