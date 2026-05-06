import importlib.util
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_legacy_baseline_capture.py"


def load_helper():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("musicnn_legacy_baseline_capture", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    imported = set(sys.modules) - before
    return module, imported


def test_helper_import_is_lightweight_and_runtime_free():
    _, imported = load_helper()

    assert "tensorflow" not in imported
    assert "essentia" not in imported
    assert "onnx" not in imported
    assert "onnxruntime" not in imported
    assert "app" not in imported


def test_helper_blocked_output_is_sanitized_for_missing_fixture_dir(tmp_path):
    helper, _ = load_helper()

    args = helper.parse_args(
        [
            "--fixtures-dir",
            str(tmp_path / "missing-fixtures"),
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    payload = helper.capture_baseline(args)
    serialized = helper.json.dumps(payload)

    assert payload["baseline_capture_succeeded"] is False
    assert payload["baseline_outputs"] == []
    assert payload["blockers"][0]["code"] == "FIXTURE_PATH_NOT_VISIBLE_IN_ONE_OFF_CONTAINER"
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def test_helper_records_essentia_first_policy_in_blocked_output(tmp_path):
    helper, _ = load_helper()

    args = helper.parse_args(
        [
            "--fixtures-dir",
            str(tmp_path / "missing-fixtures"),
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    payload = helper.capture_baseline(args)

    assert payload["import_policy_used"] == [
        "essentia_first",
        "no_explicit_tensorflow_before_essentia",
        "production_like_legacy_musicnn_path",
        "fresh_python_process",
    ]
