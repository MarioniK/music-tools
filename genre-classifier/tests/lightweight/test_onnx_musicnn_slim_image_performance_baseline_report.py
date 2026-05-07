import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-slim-image-performance-baseline-report.json"
)


def test_onnx_musicnn_slim_image_performance_baseline_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.86"
    assert report["slim_image_performance_baseline"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["reused_existing_slim_image"] is True
    assert report["rebuild_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False

    image = report["image"]
    assert image["exists"] is True
    assert image["size_bytes"] == 1572225060
    assert image["full_baseline_size_bytes"] == 3479268977
    assert image["size_reduction_bytes"] == 1907043917
    assert image["size_reduction_percent"] == 54.81

    benchmark = report["slim_benchmark"]
    assert benchmark["runs"] == 3
    assert benchmark["success"] is True
    assert benchmark["repeated_run_stable"] is True
    assert len(benchmark["total_seconds"]) == 3
    assert len(benchmark["import_seconds"]) == 3
    assert len(benchmark["audio_loading_seconds"]) == 3
    assert len(benchmark["preprocessing_seconds"]) == 3
    assert len(benchmark["onnx_session_seconds"]) == 3
    assert len(benchmark["onnx_inference_seconds"]) == 3
    assert len(benchmark["mapping_seconds"]) == 3
    assert benchmark["genres"]
    assert benchmark["genres_pretty"]

    full_pipeline = report["full_pipeline_slim_image"]
    assert full_pipeline["success"] is True
    assert full_pipeline["tensorflow_import_ok"] is False
    assert full_pipeline["essentia_import_ok"] is True
    assert full_pipeline["essentia_standard_import_ok"] is True
    assert full_pipeline["tensorflow_input_musiccnn_available"] is True
    assert full_pipeline["patch_shape"] == [187, 96]
    assert full_pipeline["activations_shape"] == [50]
    assert full_pipeline["embeddings_shape"] == [200]
    assert full_pipeline["genres_non_empty"] is True
    assert full_pipeline["genres_pretty_non_empty"] is True

    full_baseline = report["full_image_baseline_from_4_83"]
    assert full_baseline["total_seconds"] == [1.873967, 1.745251, 1.654825]
    assert full_baseline["preprocessing_seconds"] == [0.108405, 0.100992, 0.096274]
    assert full_baseline["onnx_inference_seconds"] == [0.058606, 0.050385, 0.047237]
    assert full_baseline["max_rss_kb"] == 280012

    comparison = report["comparison_to_full_image_baseline"]
    assert comparison["max_rss_kb_full"] == 280012
    assert comparison["runtime_regression_detected"] is False
    assert comparison["performance_signal"] in {"same/faster", "slower", "inconclusive"}
    assert comparison["avg_total_seconds_full"] > 0
    assert comparison["avg_total_seconds_slim"] > 0
    assert comparison["avg_preprocessing_seconds_full"] > 0
    assert comparison["avg_preprocessing_seconds_slim"] > 0
    assert comparison["avg_onnx_inference_seconds_full"] > 0
    assert comparison["avg_onnx_inference_seconds_slim"] > 0

    package_status = report["package_status"]
    assert package_status["tensorflow_installed"] is False
    assert package_status["tensorflow_import_ok"] is False
    assert package_status["essentia_tensorflow_installed"] is True
    assert package_status["essentia_standard_used"] is True
    assert package_status["tensorflow_input_musiccnn_used"] is True
    assert package_status["onnxruntime_used"] is True

    decision_signal = report["decision_signal"]
    assert decision_signal["slim_runtime_functional"] is True
    assert decision_signal["image_size_benefit_confirmed"] is True
    assert decision_signal["runtime_regression_detected"] is False
    assert "preferred optional ONNX image candidate" in decision_signal["recommendation"]

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == ["tensorflow_not_installed_in_slim_image"]
