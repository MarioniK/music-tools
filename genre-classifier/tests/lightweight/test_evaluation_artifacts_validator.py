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
    assert summary.model_provenance_checked == 1


def test_report_required_sections_are_validated(tmp_path):
    validator = load_validator()
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n\n## Summary\n", encoding="utf-8")

    try:
        validator._validate_report(report_path)
    except validator.ValidationError as exc:
        assert "Missing marker" in str(exc)
    else:
        raise AssertionError("report without required markers should fail validation")


def test_report_warning_categories_are_validated(tmp_path):
    validator = load_validator()
    report_path = tmp_path / "report.md"
    text = (SERVICE_ROOT / "docs/lightweight/evaluation/reports/example-evaluation-report.md").read_text(
        encoding="utf-8"
    )
    report_path.write_text(text.replace("comparison_incomplete", "comparison omitted"), encoding="utf-8")

    try:
        validator._validate_report(report_path)
    except validator.ValidationError as exc:
        assert "comparison_incomplete" in str(exc)
    else:
        raise AssertionError("report without every known warning category should fail validation")


def test_comparison_helper_calculates_overlap_for_example_outputs():
    validator = load_validator()
    evaluation_root = SERVICE_ROOT / "docs/lightweight/evaluation"

    summary = validator.compare_output_files(
        evaluation_root / "outputs/example-legacy-baseline-output.json",
        evaluation_root / "outputs/example-candidate-output.json",
    )

    assert summary.baseline_count == 12
    assert summary.candidate_count == 10
    assert summary.overlap_count == 10
    assert summary.overlap_ratio == 10 / 12
    assert summary.baseline_empty is False
    assert summary.candidate_empty is False


def test_comparison_helper_detects_empty_outputs():
    validator = load_validator()

    summary = validator.compare_genre_overlap(
        {"fixture_results": [{"genres": []}]},
        {"fixture_results": [{"genres": [{"tag": "pop", "prob": 0.9}]}]},
    )

    assert summary.baseline_count == 0
    assert summary.candidate_count == 1
    assert summary.overlap_count == 0
    assert summary.overlap_ratio == 0.0
    assert summary.baseline_empty is True
    assert summary.candidate_empty is False


def test_validator_cli_succeeds_for_current_artifacts(capsys):
    validator = load_validator()

    exit_code = validator.main(["--root", str(SERVICE_ROOT)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "validation ok:" in captured.out
    assert "files=5" in captured.out
    assert "json_outputs=2" in captured.out
    assert "fixture_results=16" in captured.out
    assert "model_provenance=1" in captured.out
    assert captured.err == ""


def test_model_provenance_sample_is_validated():
    validator = load_validator()
    provenance_path = (
        SERVICE_ROOT / "docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json"
    )

    validator._validate_model_provenance(provenance_path)


def test_model_provenance_requires_all_fields(tmp_path):
    validator = load_validator()
    source_path = (
        SERVICE_ROOT / "docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json"
    )
    data = validator._load_json(source_path)
    del data["license"]

    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_model_provenance(provenance_path)
    except validator.ValidationError as exc:
        assert "license" in str(exc)
    else:
        raise AssertionError("provenance without required fields should fail validation")


def test_model_provenance_rejects_production_approved_status(tmp_path):
    validator = load_validator()
    source_path = (
        SERVICE_ROOT / "docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json"
    )
    data = validator._load_json(source_path)
    data["approval_status"] = "production_approved"

    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_model_provenance(provenance_path)
    except validator.ValidationError as exc:
        assert "production-approved" in str(exc)
    else:
        raise AssertionError("production-approved provenance should fail validation")
