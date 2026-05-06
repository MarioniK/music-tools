import copy
import importlib.util
import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_pragmatic_preprocessing_prototype_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_pragmatic_preprocessing_prototype_report(REPORT_PATH)


def test_pragmatic_preprocessing_prototype_report_rejects_private_paths(tmp_path):
    validator = load_validator()
    data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["next_step_recommendation"] = "/opt/music-tools should never appear in a report"

    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(mutated), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_pragmatic_preprocessing_prototype_report(report_path)
    except validator.ValidationError as exc:
        assert "private repository paths" in str(exc)
    else:
        raise AssertionError("report with private paths should fail validation")
