import copy
import importlib.util
import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-isolated-essentia-runtime-approval-report.json"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_isolated_essentia_runtime_approval_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_isolated_essentia_runtime_approval_report(REPORT_PATH)


def test_isolated_essentia_runtime_approval_report_records_local_only_boundary():
    data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert data["status"] == "approved_for_next_step"
    assert data["selected_option"] == "A"
    assert data["isolated_runtime_path"] == "/tmp/music-tools-onnx-parity/venv"
    assert data["isolated_runtime_diagnostics"]["venv_exists"] is True
    assert data["isolated_runtime_diagnostics"]["pip_module_available"] is False
    assert data["approved_next_step"] == "Roadmap 4.59 may perform isolated venv Essentia install/check"


def test_isolated_essentia_runtime_approval_report_rejects_production_changes(tmp_path):
    validator = load_validator()
    data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["production_changes"] = True

    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(mutated), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_isolated_essentia_runtime_approval_report(report_path)
    except validator.ValidationError as exc:
        assert "production_changes" in str(exc)
    else:
        raise AssertionError("production_changes=true must fail validation")
