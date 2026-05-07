import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-image-performance-baseline-report.json"
)


def test_onnx_musicnn_optional_image_performance_baseline_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.83"
    assert report["performance_resource_baseline"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["reused_existing_image"] is True
    assert report["rebuild_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["onnx_benchmark"]["runs"] == 3
    assert report["onnx_benchmark"]["success"] is True
    assert report["onnx_benchmark"]["repeated_run_stable"] is True
    assert len(report["onnx_benchmark"]["total_seconds"]) == 3
    assert len(report["onnx_benchmark"]["import_seconds"]) == 3
    assert len(report["onnx_benchmark"]["audio_loading_seconds"]) == 3
    assert len(report["onnx_benchmark"]["preprocessing_seconds"]) == 3
    assert len(report["onnx_benchmark"]["onnx_session_seconds"]) == 3
    assert len(report["onnx_benchmark"]["onnx_inference_seconds"]) == 3
    assert len(report["onnx_benchmark"]["mapping_seconds"]) == 3
    assert report["decision_signal"]["onnx_runtime_functional"] is True
    assert report["decision_signal"]["performance_benefit_confirmed"] is False
    assert report["legacy_comparison"]["attempted"] is False
    assert report["production_boundaries"]["tidal_parser_touched"] is False

