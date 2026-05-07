import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.104-v0.5.0-onnx-release-documentation-consolidation.md"
)
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "v0.5.0-onnx-release-documentation-consolidation-report.json"
)


def test_v050_onnx_release_documentation_consolidation_report_is_structurally_valid() -> None:
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.104"
    assert report["v050_onnx_release_documentation_consolidation"] is True
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

    current_default_runtime = report["current_default_runtime"]
    assert current_default_runtime["provider"] == "onnx_musicnn"
    assert current_default_runtime["target"] == "onnx-runtime-slim"
    assert current_default_runtime["legacy_fallback_preserved"] is True
    assert current_default_runtime["legacy_pb_model_removed"] is False
    assert current_default_runtime["essentia_tensorflow_removed"] is False

    release_summary = report["release_summary"]
    assert release_summary["version"] == "v0.5.0"
    assert release_summary["onnx_default_documented"] is True
    assert release_summary["external_artifacts_documented"] is True
    assert release_summary["legacy_rollback_documented"] is True
    assert release_summary["integration_smoke_documented"] is True
    assert release_summary["cpu_observation_documented"] is True
    assert release_summary["response_shape_unchanged_documented"] is True

    docs = report["docs"]
    assert docs["onnx_runtime_doc_created"] is True
    assert docs["v050_release_doc_created"] is True
    assert docs["changelog_updated_or_created"] is True
    assert docs["readme_updated_if_needed"] is True

    artifact_contract = report["artifact_contract"]
    assert artifact_contract["host_path"] == "/opt/music-tools-artifacts/genre-classifier/onnx"
    assert artifact_contract["container_path"] == "/opt/genre-classifier/onnx"
    assert artifact_contract["model_checksum"] == "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1"
    assert artifact_contract["metadata_checksum"] == "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe"
    assert artifact_contract["artifacts_committed"] is False

    cleanup_strategy = report["cleanup_strategy"]
    assert cleanup_strategy["git_history_rewrite_recommended"] is False
    assert cleanup_strategy["use_v050_tag_as_new_stable_anchor"] is True
    assert cleanup_strategy["mass_delete_lightweight_docs_in_this_step"] is False
    assert cleanup_strategy["future_cleanup_slice_recommended"] is True

    openvino_igpu_decision = report["openvino_igpu_decision"]
    assert openvino_igpu_decision["included_in_v050"] is False
    assert openvino_igpu_decision["reason"] == (
        "ONNX CPU runtime is already fast and low CPU in production observation."
    )
    assert openvino_igpu_decision["future_optional_experiment"] is True

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
        "This step consolidates documentation only; it does not tag v0.5.0.",
        "Old lightweight roadmap/evidence files are not deleted in this step.",
    ]
