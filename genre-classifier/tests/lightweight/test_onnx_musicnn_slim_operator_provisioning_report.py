import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-slim-operator-provisioning-report.json"
)
DOC_PATH = SERVICE_ROOT / "docs/lightweight/roadmap-4.95-onnx-slim-operator-provisioning.md"


def test_onnx_musicnn_slim_operator_provisioning_report_is_structurally_valid():
    assert DOC_PATH.exists()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.95"
    assert report["onnx_slim_operator_provisioning_docs"] is True
    assert report["documentation_only"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["default_switch_approval"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["inference_run"] is False
    assert report["preprocessing_run"] is False

    operator_guide = report["operator_guide"]
    assert operator_guide["doc_path"] == "genre-classifier/docs/lightweight/roadmap-4.95-onnx-slim-operator-provisioning.md"
    assert operator_guide["covers_artifact_provisioning"] is True
    assert operator_guide["covers_checksum_verification"] is True
    assert operator_guide["covers_compose_profile_usage"] is True
    assert operator_guide["covers_health_check"] is True
    assert operator_guide["covers_classify_smoke"] is True
    assert operator_guide["covers_troubleshooting"] is True
    assert operator_guide["covers_rollback"] is True
    assert operator_guide["covers_safety_boundaries"] is True

    artifact_contract = report["artifact_contract"]
    assert artifact_contract["host_path"] == "/opt/music-tools-artifacts/genre-classifier/onnx"
    assert artifact_contract["container_path"] == "/opt/genre-classifier/onnx"
    assert artifact_contract["model_filename"] == "msd-musicnn-1.onnx"
    assert artifact_contract["metadata_filename"] == "msd-musicnn-1.json"
    assert artifact_contract["model_sha256"] == "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1"
    assert artifact_contract["metadata_sha256"] == "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe"
    assert artifact_contract["artifacts_inside_repo_allowed"] is False
    assert artifact_contract["artifacts_committed_allowed"] is False
    assert artifact_contract["runtime_downloads_by_default"] is False
    assert artifact_contract["artifacts_baked_into_image"] is False

    runtime_contract = report["runtime_contract"]
    assert runtime_contract["service"] == "genre-classifier-onnx"
    assert runtime_contract["profile"] == "onnx"
    assert runtime_contract["target"] == "onnx-runtime-slim"
    assert runtime_contract["provider"] == "onnx_musicnn"
    assert runtime_contract["default_provider_remains"] == "legacy_musicnn"
    assert runtime_contract["default_service_target_remains"] == "legacy-runtime"
    assert runtime_contract["response_shape"] == ["ok", "message", "genres", "genres_pretty"]

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
        "Documentation describes optional runtime operation; it does not grant production readiness or default switch approval."
    ]
