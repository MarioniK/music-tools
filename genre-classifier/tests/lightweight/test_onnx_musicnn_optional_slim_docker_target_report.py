import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-slim-docker-target-report.json"
)


def test_onnx_musicnn_optional_slim_docker_target_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.85"
    assert report["optional_onnx_slim_docker_target"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_build_run"] is True
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False

    implementation = report["implementation"]
    assert implementation["dockerfile_changed"] is True
    assert implementation["compose_changed"] is False
    assert implementation["slim_target_added"] is True
    assert implementation["slim_target"] == "onnx-runtime-slim"
    assert implementation["tensorflow_uninstall_in_optional_slim_path_only"] is True
    assert implementation["default_runtime_unchanged"] is True
    assert implementation["default_provider_unchanged"] is True
    assert implementation["requirements_optional_onnx_default_install_path"] is False
    assert implementation["artifacts_baked_into_image"] is False
    assert implementation["runtime_downloads_by_default"] is False

    image = report["image"]
    assert image["full_baseline_tag"] == "music-tools-genre-classifier-onnx:roadmap-4.85-full"
    assert image["full_baseline_size_bytes"] == 3479268977
    assert image["slim_image_tag"] == "music-tools-genre-classifier-onnx:roadmap-4.85-slim"
    assert image["slim_image_id"] == "sha256:f27d8bafd15565013462670982536c72e547d414d92dd35adf0cdb5896f3a9be"
    assert image["slim_image_size_bytes"] == 1572225060
    assert image["size_reduction_bytes"] == 1907043917
    assert image["size_reduction_percent"] == 54.81

    package_checks = report["package_checks"]
    assert package_checks["tensorflow_absent"] is True
    assert package_checks["essentia_tensorflow_present"] is True
    assert package_checks["onnxruntime_present"] is True

    pipeline = report["full_pipeline_slim_image"]
    assert pipeline["success"] is True
    assert pipeline["tensorflow_import_ok"] is False
    assert pipeline["essentia_import_ok"] is True
    assert pipeline["essentia_standard_import_ok"] is True
    assert pipeline["tensorflow_input_musiccnn_available"] is True
    assert pipeline["patch_shape"] == [187, 96]
    assert pipeline["activations_shape"] == [50]
    assert pipeline["embeddings_shape"] == [200]
    assert pipeline["genres_non_empty"] is True
    assert pipeline["genres_pretty_non_empty"] is True

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "Previous zero reduction was caused by Docker layer inheritance from a tensorflow-containing parent stage; the slim build now uses filtered requirements on runtime-base."
    ]
