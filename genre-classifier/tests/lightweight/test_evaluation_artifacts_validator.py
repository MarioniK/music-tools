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
    assert summary.local_artifact_metadata_checked == 1
    assert summary.label_mapping_checked == 1
    assert summary.evidence_packages_checked == 1


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
    assert "local_artifact_metadata=1" in captured.out
    assert "label_mapping=1" in captured.out
    assert "evidence_packages=1" in captured.out
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


def _local_artifact_metadata_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/model-provenance/template-local-musicnn-onnx-artifact-metadata.json"
    )


def _write_local_artifact_metadata(tmp_path, validator, data):
    metadata_path = tmp_path / "local-artifact-metadata.json"
    metadata_path.write_text(validator.json.dumps(data), encoding="utf-8")
    return metadata_path


def _local_artifact_by_role(data, role):
    for artifact in data["artifacts"]:
        if artifact["artifact_role"] == role:
            return artifact
    raise AssertionError(f"missing artifact role in fixture: {role}")


def _assert_local_artifact_metadata_fails(tmp_path, validator, data, expected):
    metadata_path = _write_local_artifact_metadata(tmp_path, validator, data)

    try:
        validator._validate_local_artifact_metadata_template(metadata_path)
    except validator.ValidationError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("local artifact metadata template should fail validation")


def test_local_artifact_metadata_template_is_validated():
    validator = load_validator()

    validator._validate_local_artifact_metadata_template(_local_artifact_metadata_path())


def test_local_artifact_metadata_requires_required_artifact_roles(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    data["artifacts"] = [
        artifact for artifact in data["artifacts"] if artifact["artifact_role"] != "official_local_json"
    ]

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "official_local_json")


def test_local_artifact_metadata_rejects_inference_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    data["approved_for_inference"] = True

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "approved_for_inference")


def test_local_artifact_metadata_rejects_production_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    data["approved_for_production"] = True

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "approved_for_production")


def test_local_artifact_metadata_rejects_production_decision(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    data["not_production_decision"] = False

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "not_production_decision")


def test_local_artifact_metadata_rejects_sha256_placeholder_string(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")["sha256"] = "placeholder"

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "fake placeholder hash")


def test_local_artifact_metadata_rejects_sha256_all_zero_string(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")["sha256"] = "0" * 64

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "fake placeholder hash")


def test_local_artifact_metadata_rejects_fake_file_size(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")["file_size_bytes"] = 123

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "file_size_bytes")


def test_local_artifact_metadata_rejects_artifact_in_repo(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")["artifact_in_repo"] = True

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "artifact_in_repo")


def test_local_artifact_metadata_rejects_committed_to_repo(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")["committed_to_repo"] = True

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "committed_to_repo")


def test_local_artifact_metadata_rejects_local_path_inside_repo(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    _local_artifact_by_role(data, "official_local_onnx")[
        "local_path"
    ] = "/opt/music-tools/genre-classifier/models/msd-musicnn-1.onnx"

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "inside the repository")


def test_local_artifact_metadata_requires_warnings_container(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    del data["warnings"]

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "warnings")


def test_local_artifact_metadata_requires_no_go_items_container(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    del data["no_go_items"]

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "no_go_items")


def test_local_artifact_metadata_rejects_approved_validation_status(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_metadata_path())
    data["validation_status"]["approved_for_inference"] = True

    _assert_local_artifact_metadata_fails(tmp_path, validator, data, "approved state")


def test_label_mapping_sample_is_validated():
    validator = load_validator()
    mapping_path = SERVICE_ROOT / "docs/lightweight/evaluation/label-mapping/example-onnx-label-mapping.json"

    validator._validate_label_mapping(mapping_path)


def test_label_mapping_requires_label_count_to_match_labels(tmp_path):
    validator = load_validator()
    source_path = SERVICE_ROOT / "docs/lightweight/evaluation/label-mapping/example-onnx-label-mapping.json"
    data = validator._load_json(source_path)
    data["label_count"] = data["label_count"] + 1

    mapping_path = tmp_path / "label-mapping.json"
    mapping_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_label_mapping(mapping_path)
    except validator.ValidationError as exc:
        assert "label_count" in str(exc)
    else:
        raise AssertionError("label mapping with mismatched label_count should fail validation")


def test_label_mapping_rejects_unknown_decision(tmp_path):
    validator = load_validator()
    source_path = SERVICE_ROOT / "docs/lightweight/evaluation/label-mapping/example-onnx-label-mapping.json"
    data = validator._load_json(source_path)
    data["labels"][0]["mapping_decision"] = "made_up"

    mapping_path = tmp_path / "label-mapping.json"
    mapping_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_label_mapping(mapping_path)
    except validator.ValidationError as exc:
        assert "mapping_decision" in str(exc)
    else:
        raise AssertionError("label mapping with unknown decision should fail validation")


def test_evidence_package_sample_is_validated():
    validator = load_validator()
    evidence_path = SERVICE_ROOT / "docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json"

    validator._validate_evidence_package(evidence_path)
    assert validator._load_json(evidence_path)["candidate_family"] == "onnx_runtime"


def test_evidence_package_requires_all_fields(tmp_path):
    validator = load_validator()
    source_path = SERVICE_ROOT / "docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json"
    data = validator._load_json(source_path)
    del data["decision_summary"]

    evidence_path = tmp_path / "evidence-package.json"
    evidence_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_evidence_package(evidence_path)
    except validator.ValidationError as exc:
        assert "decision_summary" in str(exc)
    else:
        raise AssertionError("evidence package without required fields should fail validation")


def test_evidence_package_rejects_invalid_decision_status(tmp_path):
    validator = load_validator()
    source_path = SERVICE_ROOT / "docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json"
    data = validator._load_json(source_path)
    data["decision_status"] = "approved"

    evidence_path = tmp_path / "evidence-package.json"
    evidence_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_evidence_package(evidence_path)
    except validator.ValidationError as exc:
        assert "decision_status" in str(exc)
    else:
        raise AssertionError("evidence package with invalid decision_status should fail validation")


def test_evidence_package_rejects_production_decision(tmp_path):
    validator = load_validator()
    source_path = SERVICE_ROOT / "docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json"
    data = validator._load_json(source_path)
    data["not_production_decision"] = False

    evidence_path = tmp_path / "evidence-package.json"
    evidence_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_evidence_package(evidence_path)
    except validator.ValidationError as exc:
        assert "not_production_decision" in str(exc)
    else:
        raise AssertionError("production-decision evidence package should fail validation")
