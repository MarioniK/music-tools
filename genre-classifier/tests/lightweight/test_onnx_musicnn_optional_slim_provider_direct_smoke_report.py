import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-slim-provider-direct-smoke-report.json"
)


def test_onnx_musicnn_optional_slim_provider_direct_smoke_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.91"
    assert report["optional_slim_provider_direct_smoke"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_compose_run_command_used"] is True
    assert report["docker_compose_up_run"] is False
    assert report["server_started"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["default_service_touched"] is False

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
    assert mounted_artifacts["model_checksum_match"] is True
    assert mounted_artifacts["metadata_checksum_match"] is True

    runtime_imports = report["runtime_imports"]
    assert runtime_imports["tensorflow_absent"] is True
    assert runtime_imports["essentia_standard_import_ok"] is True
    assert runtime_imports["tensorflow_input_musiccnn_available"] is True
    assert runtime_imports["onnxruntime_import_ok"] is True
    assert runtime_imports["cpu_execution_provider_available"] is True
    assert runtime_imports["provider_module_import_ok"] is True

    smoke = report["provider_direct_smoke"]
    assert smoke["success"] is True
    assert smoke["audio_path"].endswith("john_bartmann__earning_happiness__cc0.mp3")
    assert smoke["patch_shape"] == [187, 96]
    assert smoke["activations_shape"] == [50]
    assert smoke["embeddings_shape"] == [200]
    assert smoke["genres_non_empty"] is True
    assert smoke["genres_pretty_non_empty"] is True
    assert smoke["response_compatible_shape"] is True
    assert isinstance(smoke["genres"], list)
    assert isinstance(smoke["genres_pretty"], list)
    assert smoke["genres"]
    assert smoke["genres_pretty"]

    timing = report["timing"]
    assert timing["total_seconds"] is not None
    assert timing["preprocessing_seconds"] is not None
    assert timing["onnx_inference_seconds"] is not None
    assert timing["mapping_seconds"] is not None
    assert timing["max_rss_kb"] is not None

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == []
