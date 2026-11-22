import importlib.util
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_onnx_output_capture.py"


def load_helper():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("musicnn_onnx_output_capture", HELPER_PATH)
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
