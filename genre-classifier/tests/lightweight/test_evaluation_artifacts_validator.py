import importlib.util
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_validate_current_lightweight_evaluation_artifacts():
    validator = load_validator()

    summary = validator.validate_all(SERVICE_ROOT)

    assert summary.files_checked == 5
    assert summary.json_outputs_checked == 2
    assert summary.fixture_results_checked == 16


def test_validator_cli_succeeds_for_current_artifacts(capsys):
    validator = load_validator()

    exit_code = validator.main(["--root", str(SERVICE_ROOT)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "validation ok:" in captured.out
    assert "files=5" in captured.out
    assert "json_outputs=2" in captured.out
    assert "fixture_results=16" in captured.out
    assert captured.err == ""
