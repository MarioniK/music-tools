import copy
import importlib.util
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/roadmap-4.57-tensorflow-input-musicnn-availability-probe-report.json"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _future_success_case_report(validator):
    data = copy.deepcopy(validator._load_json(REPORT_PATH))
    data["tensorflow_input_musiccnn"]["available_in_isolated_env"] = True
    data["tensorflow_input_musiccnn"]["available_in_system_python"] = True
    data["tensorflow_input_musiccnn"]["import_error_category"] = None
    data["tensorflow_input_musiccnn"]["hasattr_result"] = True
    data["tensorflow_input_musiccnn"]["isolated_env"]["import_status"] = "imported"
    data["tensorflow_input_musiccnn"]["isolated_env"]["available"] = True
    data["tensorflow_input_musiccnn"]["isolated_env"]["import_error_category"] = None
    data["tensorflow_input_musiccnn"]["isolated_env"]["import_error_message"] = None
    data["tensorflow_input_musiccnn"]["isolated_env"]["hasattr_result"] = True
    data["tensorflow_input_musiccnn"]["system_python"]["import_status"] = "imported"
    data["tensorflow_input_musiccnn"]["system_python"]["available"] = True
    data["tensorflow_input_musiccnn"]["system_python"]["import_error_category"] = None
    data["tensorflow_input_musiccnn"]["system_python"]["import_error_message"] = None
    data["tensorflow_input_musiccnn"]["system_python"]["hasattr_result"] = True
    data["preprocessing_probe_result"]["attempted"] = True
    data["preprocessing_probe_result"]["succeeded"] = True
    data["preprocessing_probe_result"]["produced_shape"] = [187, 96]
    data["preprocessing_probe_result"]["expected_shape"] = [187, 96]
    data["preprocessing_probe_result"]["fixture_count"] = 3
    data["preprocessing_probe_result"]["repeated_run_stability_checked"] = True
    data["preprocessing_probe_result"]["stable"] = True
    data["preprocessing_probe_result"]["blockers"] = []
    data["fallback"]["generic_melbands_fallback_evaluated"] = True
    data["fallback"]["generic_melbands_fallback_used"] = False
    data["fallback"]["fallback_status"] = "not_used"
    data["fallback"]["fallback_risks"] = []
    data["blockers"] = []
    return data


def test_validate_current_lightweight_evaluation_artifacts():
    validator = load_validator()

    summary = validator.validate_all(SERVICE_ROOT)

    assert summary.files_checked == 5
    assert summary.json_outputs_checked == 2
    assert summary.fixture_results_checked == 16
    assert summary.model_provenance_checked == 1
    assert summary.local_artifact_metadata_checked == 1
    assert summary.local_artifact_evidence_reports_checked == 1
    assert summary.real_local_artifact_evidence_reports_checked == 1
    assert summary.parity_scaffold_dry_run_outputs_checked == 1
    assert summary.musicnn_onnx_parity_spike_reports_checked == 1
    assert summary.musicnn_onnx_parity_environment_preparation_reports_checked == 1
    assert summary.musicnn_onnx_fixtures_and_baseline_runtime_decision_reports_checked == 1
    assert summary.musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports_checked == 1
    assert summary.musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports_checked == 1
    assert summary.musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports_checked == 1
    assert summary.musicnn_legacy_baseline_capture_reports_checked == 1
    assert summary.musicnn_onnx_preprocessing_alignment_reports_checked == 1
    assert summary.musicnn_onnx_pragmatic_preprocessing_prototype_reports_checked == 1
    assert summary.musicnn_tensorflow_input_musiccnn_availability_probe_reports_checked == 1
    assert summary.musicnn_onnx_isolated_essentia_runtime_approval_reports_checked == 1
    assert summary.musicnn_onnx_output_capture_reports_checked == 1
    assert summary.musicnn_onnx_fixture_visibility_strategy_reports_checked == 1
    assert summary.musicnn_legacy_baseline_import_order_diagnostic_reports_checked == 1
    assert summary.label_mapping_checked == 1
    assert summary.evidence_packages_checked == 1
    assert summary.fixture_manifest_templates_checked == 1


def test_validate_future_success_case_roadmap_4_57_report(tmp_path):
    validator = load_validator()
    data = _future_success_case_report(validator)

    report_path = tmp_path / "roadmap-4.57-success-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    validator._validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(report_path)


def test_validate_roadmap_4_57_report_rejects_wrong_shape_when_succeeded(tmp_path):
    validator = load_validator()
    data = _future_success_case_report(validator)
    data["preprocessing_probe_result"]["produced_shape"] = [188, 96]

    report_path = tmp_path / "roadmap-4.57-wrong-shape.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(report_path)
    except validator.ValidationError as exc:
        message = str(exc)
        assert "produced_shape must be [187, 96]" in message
    else:
        raise AssertionError("successful report with wrong shape should fail validation")


def test_validate_roadmap_4_57_report_rejects_provider_approval_true(tmp_path):
    validator = load_validator()
    data = _future_success_case_report(validator)
    data["approved_for_provider_implementation"] = True

    report_path = tmp_path / "roadmap-4.57-provider-approval.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(report_path)
    except validator.ValidationError as exc:
        assert "approved_for_provider_implementation" in str(exc)
    else:
        raise AssertionError("provider approval must not be accepted")


def test_validate_roadmap_4_57_report_rejects_unknown_blocker_code(tmp_path):
    validator = load_validator()
    data = _future_success_case_report(validator)
    data["blockers"] = [{"code": "UNKNOWN_BLOCKER", "message": "nope"}]

    report_path = tmp_path / "roadmap-4.57-unknown-blocker.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(report_path)
    except validator.ValidationError as exc:
        assert "code is not allowed" in str(exc)
    else:
        raise AssertionError("unknown blocker codes must be rejected")


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
    assert "musicnn_onnx_preprocessing_alignment_reports=1" in captured.out
    assert "local_artifact_evidence_reports=1" in captured.out
    assert "real_local_artifact_evidence_reports=1" in captured.out
    assert "parity_scaffold_dry_run_outputs=1" in captured.out
    assert "musicnn_onnx_parity_spike_reports=1" in captured.out
    assert "label_mapping=1" in captured.out
    assert "musicnn_onnx_fixtures_and_baseline_runtime_decision_reports=1" in captured.out
    assert "musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports=1" in captured.out
    assert "musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports=1" in captured.out
    assert "musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports=1" in captured.out
    assert "musicnn_legacy_baseline_capture_reports=1" in captured.out
    assert "musicnn_onnx_output_capture_reports=1" in captured.out
    assert "musicnn_onnx_pragmatic_preprocessing_prototype_reports=1" in captured.out
    assert "musicnn_tensorflow_input_musiccnn_availability_probe_reports=1" in captured.out
    assert "musicnn_onnx_isolated_essentia_runtime_approval_reports=1" in captured.out
    assert "musicnn_onnx_fixture_visibility_strategy_reports=1" in captured.out
    assert "musicnn_legacy_baseline_import_order_diagnostic_reports=1" in captured.out
    assert "evidence_packages=1" in captured.out
    assert "fixture_manifest_templates=1" in captured.out
    assert captured.err == ""


def _scoped_baseline_capture_approval_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-onnx-parity-fixtures-and-scoped-baseline-capture-approval-report.json"
    )


def test_scoped_baseline_capture_approval_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report(
        _scoped_baseline_capture_approval_path()
    )


def test_scoped_baseline_capture_approval_requires_missing_fixture_blocker(tmp_path):
    validator = load_validator()
    data = validator._load_json(_scoped_baseline_capture_approval_path())
    data["fixture_blockers"] = []
    data["readiness_decision"]["blockers"] = []

    report_path = tmp_path / "approval-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report(report_path)
    except validator.ValidationError as exc:
        assert "FIXTURE_FILES_MISSING" in str(exc) or "blockers must be non-empty" in str(exc)
    else:
        raise AssertionError("missing fixture report should require a fixture blocker")


def _fixture_placement_and_scoped_baseline_readiness_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-onnx-parity-fixture-placement-and-scoped-baseline-readiness-report.json"
    )


def test_fixture_placement_and_scoped_baseline_readiness_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report(
        _fixture_placement_and_scoped_baseline_readiness_path()
    )


def test_fixture_placement_readiness_report_rejects_local_fixture_paths(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_placement_and_scoped_baseline_readiness_path())
    data["sanitized_fixtures"][0]["fixture_id"] = (
        "/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3"
    )

    report_path = tmp_path / "readiness-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report(report_path)
    except validator.ValidationError as exc:
        assert "forbidden local or repo path" in str(exc)
    else:
        raise AssertionError("fixture placement readiness report should reject local paths")


def _legacy_baseline_capture_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-legacy-baseline-capture-report.json"
    )


def test_legacy_baseline_capture_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_legacy_baseline_capture_report(_legacy_baseline_capture_report_path())


def test_legacy_baseline_capture_report_records_4_50_non_production_safety_flags():
    validator = load_validator()
    data = validator._load_json(_legacy_baseline_capture_report_path())
    serialized = validator.json.dumps(data)

    assert data["roadmap"] == "4.50"
    assert data["baseline_capture_scope"] == "one_off_compose_run_bind_mount"
    assert data["selected_fixture_visibility_strategy"] == "one_off_compose_run_bind_mount"
    assert data["import_policy"] == [
        "essentia_first",
        "no_explicit_tensorflow_before_essentia",
        "production_like_legacy_musicnn_path",
        "fresh_python_process",
    ]
    assert data["not_production_decision"] is True
    assert data["approved_for_production"] is False
    assert data["approved_for_provider_implementation"] is False
    assert data["approved_for_default_provider_switch"] is False
    assert data["approved_for_full_numeric_parity_run"] is False
    assert data["approved_for_onnx_execution"] is False
    assert data["no_onnx_execution"] is True
    assert data["no_tensorflow_vs_onnx_comparison"] is True
    assert data["baseline_capture_succeeded"] is True
    assert data["baseline_capture_status"]["succeeded"] is True
    assert len(data["baseline_outputs"]) == 3
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def test_legacy_baseline_capture_report_requires_outputs_when_successful(tmp_path):
    validator = load_validator()
    data = validator._load_json(_legacy_baseline_capture_report_path())
    data["baseline_outputs"] = []

    report_path = tmp_path / "baseline-capture-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_legacy_baseline_capture_report(report_path)
    except validator.ValidationError as exc:
        assert "baseline_outputs must match fixture_count" in str(exc)
    else:
        raise AssertionError("successful baseline capture report should require outputs")


def test_legacy_baseline_capture_report_rejects_onnx_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_legacy_baseline_capture_report_path())
    data["approved_for_onnx_execution"] = True

    report_path = tmp_path / "baseline-capture-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_legacy_baseline_capture_report(report_path)
    except validator.ValidationError as exc:
        assert "approved_for_onnx_execution" in str(exc)
    else:
        raise AssertionError("baseline capture report should reject ONNX approval")


def _onnx_output_capture_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-onnx-output-capture-report.json"
    )


def test_onnx_output_capture_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_output_capture_report(_onnx_output_capture_report_path())


def test_onnx_output_capture_report_records_blocked_preprocessing_alignment():
    validator = load_validator()
    data = validator._load_json(_onnx_output_capture_report_path())
    serialized = validator.json.dumps(data)

    assert data["roadmap"] == "4.51"
    assert data["agents_md_read"] is True
    assert data["onnx_capture_succeeded"] is False
    assert data["onnx_capture_status"]["blocked_preprocessing_unknown"] is True
    assert data["onnx_outputs"] == []
    assert data["blockers"][0]["code"] == "PREPROCESSING_ALIGNMENT_UNKNOWN"
    assert data["baseline_evidence"]["fixture_count"] == 3
    assert data["onnx_environment"]["onnxruntime_available"] is True
    assert data["onnx_artifacts"]["artifact_in_repo"] is False
    assert len(data["sanitized_fixtures"]) == 3
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def _onnx_preprocessing_alignment_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-onnx-preprocessing-alignment-report.json"
    )


def test_onnx_preprocessing_alignment_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_preprocessing_alignment_report(
        _onnx_preprocessing_alignment_report_path()
    )


def test_onnx_preprocessing_alignment_report_records_blocked_alignment_gate():
    validator = load_validator()
    data = validator._load_json(_onnx_preprocessing_alignment_report_path())
    serialized = validator.json.dumps(data)

    assert data["roadmap"] == "4.52"
    assert data["report_type"] == "musicnn_onnx_preprocessing_alignment_report"
    assert data["agents_md_read"] is True
    assert data["approved_for_production"] is False
    assert data["approved_for_provider_implementation"] is False
    assert data["approved_for_default_provider_switch"] is False
    assert data["approved_for_full_numeric_parity_run"] is False
    assert data["approved_for_final_parity_decision"] is False
    assert data["approved_for_classify_contract_change"] is False
    assert data["approved_for_onnx_fixture_output_capture"] is False
    assert data["alignment_status"]["candidate_alignment_path_found"] is False
    assert data["alignment_status"]["blocked"] is True
    assert data["alignment_status"]["inconclusive"] is False
    assert data["onnx_model_metadata"]["input_name"] == "melspectrogram"
    assert data["onnx_model_metadata"]["input_shape_tail"] == [187, 96]
    assert data["legacy_preprocessing_path"]["uses_tensorflow_predict_musiccnn"] is True
    assert data["legacy_preprocessing_path"]["uses_monoloader"] is True
    assert data["legacy_preprocessing_path"]["uses_ffmpeg"] is True
    assert data["legacy_preprocessing_path"]["preprocessing_exposed_as_intermediate"] is False
    assert data["blockers"][0]["code"] == "LEGACY_INTERMEDIATE_NOT_EXPOSED"
    assert "onnx_outputs" not in data
    assert "onnx_capture_succeeded" not in data
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def test_onnx_preprocessing_alignment_report_rejects_fake_onnx_output_claims(tmp_path):
    validator = load_validator()
    data = validator._load_json(_onnx_preprocessing_alignment_report_path())
    data["onnx_outputs"] = [{"fixture_id": "fake", "output_shape": [1, 2], "warnings": []}]

    report_path = tmp_path / "musicnn-onnx-preprocessing-alignment-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_preprocessing_alignment_report(report_path)
    except validator.ValidationError as exc:
        assert "ONNX output claims" in str(exc)
    else:
        raise AssertionError("alignment report with fake ONNX outputs should fail validation")


def test_onnx_preprocessing_alignment_report_rejects_production_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_onnx_preprocessing_alignment_report_path())
    data["approved_for_production"] = True

    report_path = tmp_path / "musicnn-onnx-preprocessing-alignment-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_preprocessing_alignment_report(report_path)
    except validator.ValidationError as exc:
        assert "approved_for_production" in str(exc)
    else:
        raise AssertionError("alignment report with production approval should fail validation")


def _fixture_visibility_strategy_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-onnx-fixture-visibility-strategy-report.json"
    )


def test_fixture_visibility_strategy_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_onnx_fixture_visibility_strategy_report(_fixture_visibility_strategy_path())


def test_fixture_visibility_strategy_report_requires_selected_one_off_bind_mount(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_visibility_strategy_path())
    data["selected_strategy"] = "docker_cp_to_container_temp_path"

    report_path = tmp_path / "fixture-visibility-strategy-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_fixture_visibility_strategy_report(report_path)
    except validator.ValidationError as exc:
        assert "one_off_compose_run_bind_mount" in str(exc)
    else:
        raise AssertionError("fixture visibility strategy report should require the selected one-off bind mount")


def _legacy_baseline_import_order_diagnostic_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/"
        / "musicnn-legacy-baseline-import-order-diagnostic-report.json"
    )


def test_legacy_baseline_import_order_diagnostic_report_is_validated():
    validator = load_validator()

    validator._validate_musicnn_legacy_baseline_import_order_diagnostic_report(
        _legacy_baseline_import_order_diagnostic_report_path()
    )


def test_legacy_baseline_import_order_diagnostic_records_4_49_safe_order():
    validator = load_validator()
    data = validator._load_json(_legacy_baseline_import_order_diagnostic_report_path())
    serialized = validator.json.dumps(data)

    assert data["roadmap"] == "4.49"
    assert data["decision_status"] == "safe_import_order_found"
    assert data["safe_import_order"]["found"] is True
    assert data["blockers"] == []
    assert data["approved_for_baseline_output_capture"] is False
    assert data["no_classify_calls"] is True
    assert data["no_onnx_execution"] is True
    assert data["no_tensorflow_vs_onnx_comparison"] is True
    prior = data["prior_import_order_knowledge"]
    assert prior["known_before_roadmap_4_49"] is True
    assert prior["source"] == "docs/runtime/roadmap-3.6-reproducible-modern-tensorflow-runtime-candidate.md"
    assert "do_not_import_tensorflow_explicitly_before_essentia" in prior["known_safe_policy"]
    assert "known Bitcast duplicate registration trap" in prior["roadmap_4_48_failure_interpretation"]
    assert any(case["bitcast_duplicate_seen"] for case in data["diagnostic_cases"])
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def test_legacy_baseline_import_order_diagnostic_requires_bitcast_category(tmp_path):
    validator = load_validator()
    data = validator._load_json(_legacy_baseline_import_order_diagnostic_report_path())
    data["diagnostic_cases"][0]["error_category"] = "duplicate_tensorflow_op_registration"

    report_path = tmp_path / "import-order-diagnostic-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_legacy_baseline_import_order_diagnostic_report(report_path)
    except validator.ValidationError as exc:
        assert "Bitcast cases must use bitcast_duplicate_registration" in str(exc)
    else:
        raise AssertionError("Bitcast observations should require the Bitcast-specific category")


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


def _local_artifact_evidence_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/model-provenance/example-local-musicnn-onnx-artifact-metadata-evidence-report.json"
    )


def _write_local_artifact_evidence_report(tmp_path, validator, data):
    report_path = tmp_path / "local-artifact-evidence-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")
    return report_path


def _evidence_artifact_by_role(data, role):
    for artifact in data["artifacts"]:
        if artifact["artifact_role"] == role:
            return artifact
    raise AssertionError(f"missing artifact role in fixture: {role}")


def _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, expected):
    report_path = _write_local_artifact_evidence_report(tmp_path, validator, data)

    try:
        validator._validate_local_artifact_evidence_report(report_path)
    except validator.ValidationError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("local artifact evidence report should fail validation")


def test_local_artifact_evidence_report_sample_is_validated():
    validator = load_validator()

    validator._validate_local_artifact_evidence_report(_local_artifact_evidence_report_path())


def test_local_artifact_evidence_report_rejects_sample_only_false(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["sample_only"] = False

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "sample_only")


def test_local_artifact_evidence_report_rejects_production_decision(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["not_production_decision"] = False

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "not_production_decision")


def test_local_artifact_evidence_report_rejects_inference_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["approved_for_inference"] = True

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "approved_for_inference")


def test_local_artifact_evidence_report_rejects_production_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["approved_for_production"] = True

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "approved_for_production")


def test_local_artifact_evidence_report_rejects_approved_review_status(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["review_status"] = "approved"

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "review_status")


def test_local_artifact_evidence_report_requires_required_artifact_roles(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    data["artifacts"] = [
        artifact for artifact in data["artifacts"] if artifact["artifact_role"] != "optional_official_local_pb"
    ]

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "optional_official_local_pb")


def test_local_artifact_evidence_report_rejects_sha256_placeholder_string(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["sha256"] = "TODO-placeholder"

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "fake placeholder hash")


def test_local_artifact_evidence_report_rejects_sha256_all_zero_string(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["sha256"] = "0" * 64

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "fake placeholder hash")


def test_local_artifact_evidence_report_rejects_fake_file_size(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["file_size_bytes"] = 123

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "file_size_bytes")


def test_local_artifact_evidence_report_rejects_artifact_downloaded(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["artifact_downloaded"] = True

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "artifact_downloaded")


def test_local_artifact_evidence_report_rejects_artifact_in_repo(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["artifact_in_repo"] = True

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "artifact_in_repo")


def test_local_artifact_evidence_report_rejects_committed_to_repo(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["committed_to_repo"] = True

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "committed_to_repo")


def test_local_artifact_evidence_report_rejects_local_path(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    _evidence_artifact_by_role(data, "official_local_onnx")["local_path"] = "/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx"

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "local_path")


def test_local_artifact_evidence_report_requires_warnings_container(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    del data["warnings"]

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "warnings")


def test_local_artifact_evidence_report_requires_no_go_items_container(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    del data["no_go_items"]

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "no_go_items")


def test_local_artifact_evidence_report_requires_next_step_recommendation(tmp_path):
    validator = load_validator()
    data = validator._load_json(_local_artifact_evidence_report_path())
    del data["next_step_recommendation"]

    _assert_local_artifact_evidence_report_fails(tmp_path, validator, data, "next_step_recommendation")


def _real_local_artifact_evidence_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json"
    )


def _write_real_local_artifact_evidence_report(tmp_path, validator, data):
    report_path = tmp_path / "real-local-artifact-evidence-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")
    return report_path


def _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, expected):
    report_path = _write_real_local_artifact_evidence_report(tmp_path, validator, data)

    try:
        validator._validate_real_local_artifact_evidence_report(report_path)
    except validator.ValidationError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("real local artifact evidence report should fail validation")


def _real_report_data(validator):
    return copy.deepcopy(validator._load_json(_real_local_artifact_evidence_report_path()))


def test_real_local_artifact_evidence_report_is_validated():
    validator = load_validator()

    validator._validate_real_local_artifact_evidence_report(_real_local_artifact_evidence_report_path())


def test_real_local_artifact_evidence_report_rejects_inference_approval(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["approved_for_inference"] = True

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "approved_for_inference")


def test_real_local_artifact_evidence_report_rejects_production_approval(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["approved_for_production"] = True

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "approved_for_production")


def test_real_local_artifact_evidence_report_rejects_production_decision(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["not_production_decision"] = False

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "not_production_decision")


def test_real_local_artifact_evidence_report_rejects_wrong_approval_status(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["approval_status"] = "reviewed_not_approved"

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "approval_status")


def test_real_local_artifact_evidence_report_rejects_invalid_sha256(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")["sha256"] = "not-a-valid-sha"

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "sha256")


def test_real_local_artifact_evidence_report_rejects_all_zero_sha256(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")["sha256"] = "0" * 64

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "fake placeholder hash")


def test_real_local_artifact_evidence_report_rejects_missing_or_zero_file_size(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")["file_size_bytes"] = 0

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "file_size_bytes")


def test_real_local_artifact_evidence_report_rejects_official_local_path_inside_repo(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")[
        "local_path"
    ] = "/opt/music-tools/genre-classifier/app/models/msd-musicnn-1.onnx"

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "local_path")


def test_real_local_artifact_evidence_report_rejects_official_local_artifact_in_repo(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")["artifact_in_repo"] = True

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "artifact_in_repo")


def test_real_local_artifact_evidence_report_rejects_official_local_committed_to_repo(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_onnx")["committed_to_repo"] = True

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "committed_to_repo")


def test_real_local_artifact_evidence_report_requires_pb_hash_match_observation(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["verification_results"].pop("current_bundled_pb_matches_official_local_pb_sha256")
    optional_pb = _evidence_artifact_by_role(data, "optional_official_local_pb")
    optional_pb["verification_results"].pop("matches_current_bundled_pb_sha256")
    optional_pb["provenance_notes"] = "Optional PB was measured for metadata review only."

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "PB hash match observation")


def test_real_local_artifact_evidence_report_requires_json_mismatch_warning(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    _evidence_artifact_by_role(data, "official_local_json")[
        "provenance_notes"
    ] = "Official/local JSON was measured for metadata review only."
    _evidence_artifact_by_role(data, "current_bundled_json")[
        "provenance_notes"
    ] = "Current bundled JSON was measured for metadata review only."
    data["warnings"] = ["local-only paths are non-portable and must not be used by production runtime"]
    data["no_go_items"] = ["do_not_run_inference"]

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "JSON mismatch")


def test_real_local_artifact_evidence_report_rejects_numeric_parity_claim(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["warnings"].append("numeric parity approved")

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "numeric parity approved")


def test_real_local_artifact_evidence_report_rejects_final_genres_parity_claim(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["warnings"].append("final genres parity confirmed")

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "final genres parity confirmed")


def test_real_local_artifact_evidence_report_rejects_genres_pretty_parity_claim(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["warnings"].append("genres_pretty parity approved")

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "genres_pretty parity approved")


def test_real_local_artifact_evidence_report_rejects_provider_implementation_approval(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    data["warnings"].append("provider implementation approved")

    _assert_real_local_artifact_evidence_report_fails(
        tmp_path, validator, data, "provider implementation approved"
    )


def test_real_local_artifact_evidence_report_requires_verification_commands(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    del data["verification_commands"]

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "verification_commands")


def test_real_local_artifact_evidence_report_requires_verification_results(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    del data["verification_results"]

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "verification_results")


def test_real_local_artifact_evidence_report_requires_next_step_recommendation(tmp_path):
    validator = load_validator()
    data = _real_report_data(validator)
    del data["next_step_recommendation"]

    _assert_real_local_artifact_evidence_report_fails(tmp_path, validator, data, "next_step_recommendation")


def _fixture_manifest_template_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/fixtures/template-local-musicnn-onnx-parity-fixture-manifest.json"
    )


def _write_fixture_manifest_template(tmp_path, validator, data):
    template_path = tmp_path / "fixture-manifest-template.json"
    template_path.write_text(validator.json.dumps(data), encoding="utf-8")
    return template_path


def _assert_fixture_manifest_template_fails(tmp_path, validator, data, expected):
    template_path = _write_fixture_manifest_template(tmp_path, validator, data)

    try:
        validator._validate_fixture_manifest_template(template_path)
    except validator.ValidationError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("fixture manifest template should fail validation")


def test_fixture_manifest_template_is_validated():
    validator = load_validator()

    validator._validate_fixture_manifest_template(_fixture_manifest_template_path())


def test_fixture_manifest_template_rejects_inference_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["approved_for_inference"] = True

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "approved_for_inference")


def test_fixture_manifest_template_rejects_sample_local_path(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["sample_fixture"]["local_path"] = "/tmp/music-tools-onnx-parity/fixtures/example.wav"

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "local_path")


def test_fixture_manifest_template_rejects_sample_sha256(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["sample_fixture"]["sha256"] = "0" * 64

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "sha256")


def test_fixture_manifest_template_rejects_sample_file_size(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["sample_fixture"]["file_size_bytes"] = 123

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "file_size_bytes")


def test_fixture_manifest_template_requires_required_fixture_fields(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["required_fixture_fields"] = [
        field for field in data["required_fixture_fields"] if field != "usage_permission"
    ]

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "usage_permission")


def test_fixture_manifest_template_requires_storage_policy_root(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["fixture_storage_policy"]["recommended_local_fixture_root"] = "/opt/music-tools/genre-classifier"

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "/tmp/music-tools-onnx-parity/fixtures/")


def test_fixture_manifest_template_requires_forbidden_path_markers(tmp_path):
    validator = load_validator()
    data = validator._load_json(_fixture_manifest_template_path())
    data["fixture_storage_policy"]["forbidden_paths"] = [
        marker
        for marker in data["fixture_storage_policy"]["forbidden_paths"]
        if marker != "any git-tracked path"
    ]

    _assert_fixture_manifest_template_fails(tmp_path, validator, data, "any git-tracked path")


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


def _musicnn_onnx_parity_spike_report_path():
    return SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-spike-report.json"


def _musicnn_onnx_parity_environment_preparation_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-environment-preparation-report.json"
    )


def _musicnn_onnx_fixtures_and_baseline_runtime_decision_report_path():
    return (
        SERVICE_ROOT
        / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-fixtures-and-baseline-runtime-decision-report.json"
    )


def test_musicnn_onnx_parity_spike_report_is_validated():
    validator = load_validator()
    report_path = _musicnn_onnx_parity_spike_report_path()

    validator._validate_musicnn_onnx_parity_spike_report(report_path)
    data = validator._load_json(report_path)

    assert data["roadmap"] == "4.40"
    assert data["report_type"] == "musicnn_onnx_parity_spike_report"
    assert data["not_production_decision"] is True
    assert data["approved_for_production"] is False
    assert data["approved_for_provider_implementation"] is False
    assert data["approved_for_default_provider_switch"] is False
    assert data["approved_for_inference_beyond_local_spike"] is False
    assert data["onnxruntime_added_to_production_requirements"] is False
    assert data["metrics"]["max_abs_diff"] is None


def test_blocked_musicnn_onnx_parity_spike_report_rejects_fake_metrics(tmp_path):
    validator = load_validator()
    data = validator._load_json(_musicnn_onnx_parity_spike_report_path())
    data["decision_status"] = "blocked_missing_runtime"
    data["parity_run_executed"] = False
    data["metrics"]["max_abs_diff"] = 0.0

    report_path = tmp_path / "musicnn-onnx-parity-spike-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_parity_spike_report(report_path)
    except validator.ValidationError as exc:
        assert "max_abs_diff" in str(exc)
    else:
        raise AssertionError("blocked parity spike report with fake metrics should fail validation")


def test_musicnn_onnx_parity_spike_report_rejects_production_approval(tmp_path):
    validator = load_validator()
    data = validator._load_json(_musicnn_onnx_parity_spike_report_path())
    data["approved_for_production"] = True

    report_path = tmp_path / "musicnn-onnx-parity-spike-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_parity_spike_report(report_path)
    except validator.ValidationError as exc:
        assert "approved_for_production" in str(exc)
    else:
        raise AssertionError("production-approved parity spike report should fail validation")


def test_musicnn_onnx_parity_environment_preparation_report_is_validated():
    validator = load_validator()
    report_path = _musicnn_onnx_parity_environment_preparation_report_path()

    validator._validate_musicnn_onnx_parity_environment_preparation_report(report_path)
    data = validator._load_json(report_path)

    assert data["roadmap"] == "4.41"
    assert data["report_type"] == "musicnn_onnx_parity_environment_preparation_report"
    assert data["approved_for_production"] is False
    assert data["approved_for_provider_implementation"] is False
    assert data["approved_for_default_provider_switch"] is False
    assert data["approved_for_inference_beyond_local_spike"] is False
    assert data["no_venv_committed"] is True
    assert data["prerequisites"]["isolated_env_path_sanitized"] is True


def test_musicnn_onnx_parity_environment_preparation_report_rejects_private_paths(tmp_path):
    validator = load_validator()
    data = validator._load_json(_musicnn_onnx_parity_environment_preparation_report_path())
    data["sanitized_locations"]["isolated_env"] = "/tmp/music-tools-onnx-parity/venv"

    report_path = tmp_path / "musicnn-onnx-parity-environment-preparation-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_parity_environment_preparation_report(report_path)
    except validator.ValidationError as exc:
        assert "full local path" in str(exc)
    else:
        raise AssertionError("environment preparation report with private paths should fail validation")


def test_musicnn_onnx_fixtures_and_baseline_runtime_decision_report_is_validated():
    validator = load_validator()
    report_path = _musicnn_onnx_fixtures_and_baseline_runtime_decision_report_path()

    validator._validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(report_path)
    data = validator._load_json(report_path)

    assert data["roadmap"] == "4.42"
    assert data["report_type"] == "musicnn_onnx_fixtures_and_baseline_runtime_decision_report"
    assert data["fixture_status"] == "missing"
    assert data["baseline_runtime_status"] == "unavailable"
    assert data["approved_for_numeric_parity_run"] is False
    assert data["onnxruntime_available"] is True
    assert data["sanitized_fixtures"] == []


def test_musicnn_onnx_fixtures_and_baseline_runtime_decision_report_rejects_private_paths(tmp_path):
    validator = load_validator()
    data = validator._load_json(_musicnn_onnx_fixtures_and_baseline_runtime_decision_report_path())
    data["sanitized_locations"]["fixture_workspace_label"] = "/tmp/music-tools-onnx-parity/fixtures"

    report_path = tmp_path / "musicnn-onnx-parity-fixtures-and-baseline-runtime-decision-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(report_path)
    except validator.ValidationError as exc:
        assert "full local path" in str(exc)
    else:
        raise AssertionError("decision report with private paths should fail validation")


def test_musicnn_onnx_fixtures_and_baseline_runtime_decision_report_rejects_numeric_parity_flag(tmp_path):
    validator = load_validator()
    data = validator._load_json(_musicnn_onnx_fixtures_and_baseline_runtime_decision_report_path())
    data["approved_for_numeric_parity_run"] = True

    report_path = tmp_path / "musicnn-onnx-parity-fixtures-and-baseline-runtime-decision-report.json"
    report_path.write_text(validator.json.dumps(data), encoding="utf-8")

    try:
        validator._validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(report_path)
    except validator.ValidationError as exc:
        assert "approved_for_numeric_parity_run" in str(exc)
    else:
        raise AssertionError("decision report with numeric parity flag should fail validation")
