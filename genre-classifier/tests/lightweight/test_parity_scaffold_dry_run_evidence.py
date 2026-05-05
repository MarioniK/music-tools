import copy
import importlib.util
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"
EVIDENCE_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/example-musicnn-onnx-parity-scaffold-dry-run-output.json"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_evidence(validator):
    return validator._load_json(EVIDENCE_PATH)


def write_evidence(tmp_path, validator, data):
    path = tmp_path / "scaffold-dry-run-output.json"
    path.write_text(validator.json.dumps(data), encoding="utf-8")
    return path


def assert_scaffold_evidence_fails(tmp_path, validator, data, expected):
    path = write_evidence(tmp_path, validator, data)

    try:
        validator._validate_parity_scaffold_dry_run_output(path)
    except validator.ValidationError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("parity scaffold dry-run evidence should fail validation")


def test_valid_dry_run_output_passes():
    validator = load_validator()

    validator._validate_parity_scaffold_dry_run_output(EVIDENCE_PATH)


def test_inference_attempted_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["inference_attempted"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "inference_attempted")


def test_onnxruntime_imported_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["onnxruntime_imported"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "onnxruntime_imported")


def test_tensorflow_imported_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["tensorflow_imported"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "tensorflow_imported")


def test_classify_called_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["classify_called"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "classify_called")


def test_provider_imported_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["provider_imported"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "provider_imported")


def test_approved_for_inference_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["approved_for_inference"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "approved_for_inference")


def test_approved_for_production_true_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["approved_for_production"] = True

    assert_scaffold_evidence_fails(tmp_path, validator, data, "approved_for_production")


def test_parity_claim_fails(tmp_path):
    validator = load_validator()
    data = load_evidence(validator)
    data["scaffold_output"]["warnings"].append("numeric parity approved")

    assert_scaffold_evidence_fails(tmp_path, validator, data, "numeric parity approved")


def test_fixture_mutation_does_not_change_source_evidence():
    validator = load_validator()
    data = load_evidence(validator)
    clone = copy.deepcopy(data)
    clone["scaffold_output"]["checks"][0]["ok"] = False

    assert data["scaffold_output"]["checks"][0]["ok"] is True
