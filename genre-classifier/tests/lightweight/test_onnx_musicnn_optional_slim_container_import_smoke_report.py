import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-slim-container-import-smoke-report.json"
)


def test_onnx_musicnn_optional_slim_container_import_smoke_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.90"
    assert report["optional_slim_container_import_smoke"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_compose_run_command_used"] is True
    assert report["docker_compose_up_run"] is False
    assert report["docker_build_run"] is True
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["server_started"] is False
    assert report["inference_run"] is False
    assert report["preprocessing_run"] is False

    service = report["service"]
    assert service["name"] == "genre-classifier-onnx"
    assert service["profile"] == "onnx"
    assert service["target"] == "onnx-runtime-slim"

    container_env = report["container_env"]
    assert container_env["provider_env"] == "onnx_musicnn"
    assert container_env["model_env_path"] == "/opt/genre-classifier/onnx/msd-musicnn-1.onnx"
    assert container_env["metadata_env_path"] == "/opt/genre-classifier/onnx/msd-musicnn-1.json"
    assert container_env["env_match"] is True

    mounted_artifacts = report["mounted_artifacts"]
    assert mounted_artifacts["model_exists"] is True
    assert mounted_artifacts["metadata_exists"] is True
    assert mounted_artifacts["model_sha256"] == "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1"
    assert mounted_artifacts["metadata_sha256"] == "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe"
    assert mounted_artifacts["model_checksum_match"] is True
    assert mounted_artifacts["metadata_checksum_match"] is True

    runtime_imports = report["runtime_imports"]
    assert runtime_imports["tensorflow_absent"] is True
    assert runtime_imports["tensorflow_import_ok"] is False
    assert runtime_imports["essentia_import_ok"] is True
    assert runtime_imports["essentia_standard_import_ok"] is True
    assert runtime_imports["tensorflow_input_musiccnn_available"] is True
    assert runtime_imports["onnxruntime_import_ok"] is True
    assert runtime_imports["cpu_execution_provider_available"] is True
    assert runtime_imports["provider_module_import_ok"] is True

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "Optional ONNX image was absent initially, so docker compose run performed a targeted build of genre-classifier-onnx before the smoke command executed."
    ]
