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


def test_dry_run_command_succeeds_without_heavy_dependencies():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run"],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "dry-run only" in result.stdout
    assert "no ONNX Runtime loaded" in result.stdout
    assert "no model loaded" in result.stdout
    assert "no audio processed" in result.stdout
    assert "no inference executed" in result.stdout
    assert result.stderr == ""


def test_write_output_creates_valid_classify_compatible_json(tmp_path):
    output_path = tmp_path / "nested/output.json"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run", "--write-output", str(output_path)],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    value = json.loads(output_path.read_text(encoding="utf-8"))
    assert_classify_compatible_shape(value)
    assert value == {
        "ok": True,
        "message": (
            "dry-run only; no ONNX Runtime loaded; no model loaded; "
            "no audio processed; no inference executed"
        ),
        "genres": [{"tag": "electronic", "prob": 0.0}],
        "genres_pretty": ["Electronic"],
    }


def test_script_builds_classify_compatible_payload():
    spike_script = load_spike_script()

    value = spike_script.build_dry_run_output()

    assert_classify_compatible_shape(value)


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
