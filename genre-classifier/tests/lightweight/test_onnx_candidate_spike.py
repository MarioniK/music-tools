import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = SERVICE_ROOT / "scripts/lightweight/onnx_candidate_spike.py"


def load_spike_script():
    spec = importlib.util.spec_from_file_location("onnx_candidate_spike", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def assert_classify_compatible_shape(value):
    assert isinstance(value["ok"], bool)
    assert isinstance(value["message"], str)
    assert isinstance(value["genres"], list)
    assert isinstance(value["genres_pretty"], list)
    assert all(isinstance(item, str) for item in value["genres_pretty"])

    for item in value["genres"]:
        assert isinstance(item, dict)
        assert isinstance(item["tag"], str)
        assert isinstance(item["prob"], (int, float))


def run_spike(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stderr == ""
    return json.loads(result.stdout)


def assert_spike_metadata_shape(value):
    assert value["spike"]["roadmap"] == "4.8"
    assert value["spike"]["variant"] == "B"
    assert value["spike"]["mode"] == "dry_run"
    assert value["spike"]["inference_executed"] is False
    assert value["spike"]["audio_processed"] is False
    assert value["runtime"]["package"] == "onnxruntime"
    assert isinstance(value["runtime"]["available"], bool)
    assert value["runtime"]["imported"] is False
    assert value["runtime"]["detection_method"] == 'importlib.util.find_spec("onnxruntime")'
    assert isinstance(value["resource_latency_metadata"]["started_at_utc"], str)
    assert isinstance(value["resource_latency_metadata"]["finished_at_utc"], str)
    assert isinstance(value["resource_latency_metadata"]["duration_ms"], (int, float))
    assert isinstance(value["resource_latency_metadata"]["python_version"], str)
    assert isinstance(value["resource_latency_metadata"]["platform"], str)
    assert isinstance(value["warnings"], list)


def warning_categories(value):
    return {warning["category"] for warning in value["warnings"]}


def test_dry_run_without_args_succeeds_without_heavy_dependencies():
    value = run_spike()

    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)
    assert value["spike"]["status"] == "dry_run_metadata_only"
    assert "no runtime loaded" in value["message"]
    assert "no model loaded for inference" in value["message"]
    assert "no audio processed" in value["message"]
    assert "no inference executed" in value["message"]
    assert value["model"]["path_provided"] is False
    assert value["model"]["size_bytes"] is None
    assert {"model_path_missing", "license_unknown", "model_provenance_unknown"} <= (
        warning_categories(value)
    )


def test_write_output_creates_valid_classify_compatible_json(tmp_path):
    output_path = tmp_path / "nested/output.json"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--write-output", str(output_path)],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    value = json.loads(output_path.read_text(encoding="utf-8"))
    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)
    assert value["genres"] == [{"tag": "electronic", "prob": 0.0}]
    assert value["genres_pretty"] == ["Electronic"]


def test_output_alias_creates_structured_json(tmp_path):
    output_path = tmp_path / "artifact.json"

    value = run_spike("--output", str(output_path))

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == value
    assert_classify_compatible_shape(written)
    assert_spike_metadata_shape(written)


def test_script_builds_classify_compatible_payload():
    spike_script = load_spike_script()

    value = spike_script.build_dry_run_output()

    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)


def test_runtime_detection_does_not_require_runtime_import():
    spike_script = load_spike_script()

    value = spike_script.detect_onnxruntime()

    assert value["package"] == "onnxruntime"
    assert isinstance(value["available"], bool)
    assert value["imported"] is False
    assert value["detection_method"] == 'importlib.util.find_spec("onnxruntime")'


def test_missing_model_path_produces_controlled_status_and_warning(tmp_path):
    missing_path = tmp_path / "missing.onnx"

    value = run_spike("--model-path", str(missing_path))

    assert value["spike"]["status"] == "skipped_model_path_not_found"
    assert value["model"]["path_provided"] is True
    assert value["model"]["exists"] is False
    assert value["model"]["is_file"] is False
    assert value["model"]["suffix"] == ".onnx"
    assert value["model"]["size_bytes"] is None
    assert "model_path_not_found" in warning_categories(value)
    assert "model_suffix_not_onnx" not in warning_categories(value)


def test_no_model_path_keeps_metadata_only_dry_run_mode():
    value = run_spike("--dry-run")

    assert value["spike"]["status"] == "dry_run_metadata_only"
    assert value["model"] == {
        "path_provided": False,
        "path": None,
        "exists": None,
        "is_file": None,
        "suffix": None,
        "suffix_expected": ".onnx",
        "size_bytes": None,
    }
    assert value["resource_latency_metadata"]["model_size_bytes"] is None


def test_temporary_fake_onnx_file_can_be_inspected_without_real_runtime(tmp_path):
    model_path = tmp_path / "fake.onnx"
    model_path.write_bytes(b"not a real model")

    value = run_spike("--model-path", str(model_path))

    assert value["spike"]["status"] == "local_model_inspected_no_inference"
    assert value["model"]["path_provided"] is True
    assert value["model"]["path"] == str(model_path)
    assert value["model"]["exists"] is True
    assert value["model"]["is_file"] is True
    assert value["model"]["suffix"] == ".onnx"
    assert value["model"]["size_bytes"] == len(b"not a real model")
    assert value["resource_latency_metadata"]["model_size_bytes"] == len(b"not a real model")
    assert value["spike"]["inference_executed"] is False
    assert "model_suffix_not_onnx" not in warning_categories(value)


def test_model_provenance_fields_are_recorded():
    value = run_spike(
        "--model-name",
        "example-audio-onnx",
        "--model-source-url",
        "https://example.invalid/model",
        "--license",
        "Example-License",
        "--license-url",
        "https://example.invalid/license",
        "--checksum-sha256",
        "0" * 64,
        "--provenance-status",
        "recorded",
    )

    assert value["provenance"] == {
        "model_name": "example-audio-onnx",
        "model_source_url": "https://example.invalid/model",
        "license": "Example-License",
        "license_url": "https://example.invalid/license",
        "checksum_sha256": "0" * 64,
        "provenance_status": "recorded",
    }
    assert "license_unknown" not in warning_categories(value)
    assert "model_provenance_unknown" not in warning_categories(value)


def test_script_source_does_not_import_heavy_runtime_modules():
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    forbidden_markers = (
        "import onnxruntime",
        "from onnxruntime",
        "import tensorflow",
        "from tensorflow",
        "import essentia",
        "from essentia",
        "import app.main",
        "from app.main",
        "provider_factory",
        "legacy_musicnn",
    )

    for marker in forbidden_markers:
        assert marker not in source
