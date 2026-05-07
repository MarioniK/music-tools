import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "legacy-vs-onnx-slim-direct-benchmark-report.json"
)


def test_legacy_vs_onnx_slim_direct_benchmark_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.92"
    assert report["legacy_vs_onnx_slim_direct_benchmark"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_compose_run_command_used"] is True
    assert report["docker_compose_up_run"] is False
    assert report["server_started"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["default_provider_changed"] is False
    assert report["audio_fixture"] == "/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3"

    legacy = report["legacy_benchmark"]
    assert legacy["attempted"] is True
    assert legacy["available"] is True
    assert legacy["service"] == "genre-classifier"
    assert legacy["provider"] == "legacy_musicnn"
    assert legacy["runs"] == 3
    assert legacy["success"] is True
    assert len(legacy["total_seconds"]) == 3
    assert len(legacy["inference_seconds"]) == 3
    assert len(legacy["mapping_seconds"]) == 3
    assert len(legacy["preprocessing_seconds"]) == 3
    assert all(value is None for value in legacy["preprocessing_seconds"])
    assert legacy["response_compatible_shape"] is True
    assert legacy["repeated_run_stable"] is True
    assert legacy["genres"]
    assert legacy["genres_pretty"]

    onnx = report["onnx_slim_benchmark"]
    assert onnx["attempted"] is True
    assert onnx["available"] is True
    assert onnx["service"] == "genre-classifier-onnx"
    assert onnx["provider"] == "onnx_musicnn"
    assert onnx["runs"] == 3
    assert onnx["success"] is True
    assert len(onnx["total_seconds"]) == 3
    assert len(onnx["preprocessing_seconds"]) == 3
    assert len(onnx["inference_seconds"]) == 3
    assert len(onnx["mapping_seconds"]) == 3
    assert onnx["response_compatible_shape"] is True
    assert onnx["repeated_run_stable"] is True
    assert onnx["genres"]
    assert onnx["genres_pretty"]

    comparison = report["comparison"]
    assert comparison["avg_total_seconds_legacy"] > 0
    assert comparison["avg_total_seconds_onnx_slim"] > 0
    assert comparison["speedup_ratio_legacy_div_onnx"] > 0
    assert comparison["memory_delta_kb"] is not None
    assert comparison["response_shape_match"] is True
    assert comparison["output_drift_documented"] is True
    assert "drift" in comparison["qualitative_output_drift_note"].lower()

    decision_signal = report["decision_signal"]
    assert decision_signal["onnx_slim_runtime_functional"] is True
    assert decision_signal["legacy_comparison_completed"] is True
    assert decision_signal["performance_benefit_confirmed"] in {True, False}

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["dockerfile_changed"] is False
    assert production_boundaries["compose_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] in ([], ["LEGACY_DIRECT_BENCHMARK_PATH_NOT_AVAILABLE"], ["ONNX_SLIM_DIRECT_BENCHMARK_PATH_NOT_AVAILABLE"])
    assert isinstance(report["warnings"], list)
