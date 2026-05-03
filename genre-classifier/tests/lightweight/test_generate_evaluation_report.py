import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = SERVICE_ROOT / "scripts/lightweight/generate_evaluation_report.py"
VALIDATOR_PATH = SERVICE_ROOT / "scripts/lightweight/validate_evaluation_artifacts.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_evaluation_report", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evaluation_artifacts", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_output(path, provider, fixture_results, warnings=None):
    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "artifact_type": "test_output",
                "provider": provider,
                "fixture_results": fixture_results,
                "warnings": warnings or [],
                "aggregate_metrics": {
                    "fixture_count": len(fixture_results),
                    "successful_fixtures": len(fixture_results),
                    "failed_fixtures": 0,
                    "mean_latency_ms": None,
                    "p95_latency_ms": None,
                    "peak_memory_mb": None,
                    "startup_import_time_ms": None,
                    "model_size_mb": None,
                    "dependency_runtime_weight_mb": None,
                    "docker_image_size_impact_mb": None,
                },
            }
        ),
        encoding="utf-8",
    )


def fixture_result(fixture_id, tags, ok=True):
    return {
        "fixture_id": fixture_id,
        "ok": ok,
        "message": "ok" if ok else "no result",
        "genres": [{"tag": tag, "prob": 0.9} for tag in tags],
        "genres_pretty": tags,
        "normalized_genres": tags,
        "warnings": [],
    }


def test_generator_cli_creates_report_from_example_artifacts(tmp_path):
    output_report = tmp_path / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATOR_PATH),
            "--baseline-output",
            "docs/lightweight/evaluation/outputs/example-legacy-baseline-output.json",
            "--candidate-output",
            "docs/lightweight/evaluation/outputs/example-candidate-output.json",
            "--manifest",
            "docs/lightweight/evaluation/manifests/example-manifest.yaml",
            "--output-report",
            str(output_report),
            "--candidate-name",
            "onnx_candidate",
            "--decision",
            "no production decision",
        ],
        cwd=SERVICE_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    text = output_report.read_text(encoding="utf-8")
    assert "Candidate provider: `onnx_candidate`." in text
    assert "wrote report:" in result.stdout


def test_generated_report_contains_required_sections(tmp_path):
    generator = load_generator()
    validator = load_validator()
    output_report = tmp_path / "report.md"

    assert (
        generator.main(
            [
                "--baseline-output",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/outputs/example-legacy-baseline-output.json"),
                "--candidate-output",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/outputs/example-candidate-output.json"),
                "--manifest",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/manifests/example-manifest.yaml"),
                "--output-report",
                str(output_report),
            ]
        )
        == 0
    )

    text = output_report.read_text(encoding="utf-8")
    validator._validate_normalized_report_markers(
        output_report, text, validator.REQUIRED_REPORT_MARKERS
    )


def test_generated_report_contains_offline_only_markers(tmp_path):
    generator = load_generator()
    output_report = tmp_path / "report.md"

    assert (
        generator.main(
            [
                "--baseline-output",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/outputs/example-legacy-baseline-output.json"),
                "--candidate-output",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/outputs/example-candidate-output.json"),
                "--manifest",
                str(SERVICE_ROOT / "docs/lightweight/evaluation/manifests/example-manifest.yaml"),
                "--output-report",
                str(output_report),
            ]
        )
        == 0
    )

    text = output_report.read_text(encoding="utf-8")
    for marker in (
        "offline-only static artifact comparison",
        "not production decision",
        "inference executed: no",
        "/classify called: no",
        "production provider/runtime imports: no",
        "default provider changed: no",
        "approval gate: not approved for production",
    ):
        assert marker in text


def test_top_n_overlap_calculation_works_on_small_temp_json_fixtures(tmp_path):
    generator = load_generator()
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text('schema_version: "0.1"\nfixtures:\n  - id: "a"\n', encoding="utf-8")

    write_output(
        baseline_path,
        "legacy_musicnn",
        [fixture_result("a", ["pop", "rock", "jazz"])],
    )
    write_output(
        candidate_path,
        "onnx_candidate",
        [fixture_result("a", ["pop", "metal", "jazz"])],
    )

    report = generator.generate_report(
        baseline_path, candidate_path, manifest_path, "onnx_candidate", "no production decision"
    )

    assert "| average ratio | 1.000 | 0.667 | 0.667 |" in report
    assert "| a | pop, rock, jazz | pop, metal, jazz | 1/1 | 2/3 | 2/3 | none |" in report


def test_empty_baseline_or_candidate_output_is_warning_not_traceback(tmp_path):
    generator = load_generator()
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    manifest_path = tmp_path / "manifest.yaml"
    output_report = tmp_path / "report.md"
    manifest_path.write_text('schema_version: "0.1"\nfixtures:\n  - id: "a"\n', encoding="utf-8")

    write_output(baseline_path, "legacy_musicnn", [fixture_result("a", [])])
    write_output(candidate_path, "onnx_candidate", [fixture_result("a", ["pop"])])

    exit_code = generator.main(
        [
            "--baseline-output",
            str(baseline_path),
            "--candidate-output",
            str(candidate_path),
            "--manifest",
            str(manifest_path),
            "--output-report",
            str(output_report),
        ]
    )

    assert exit_code == 0
    text = output_report.read_text(encoding="utf-8")
    assert "`empty_output`" in text
    assert "`comparison_incomplete`" in text


def test_invalid_json_input_produces_controlled_failure(tmp_path, capsys):
    generator = load_generator()
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    manifest_path = tmp_path / "manifest.yaml"
    baseline_path.write_text("{not json", encoding="utf-8")
    write_output(candidate_path, "onnx_candidate", [fixture_result("a", ["pop"])])
    manifest_path.write_text('schema_version: "0.1"\n', encoding="utf-8")

    exit_code = generator.main(
        [
            "--baseline-output",
            str(baseline_path),
            "--candidate-output",
            str(candidate_path),
            "--manifest",
            str(manifest_path),
            "--output-report",
            str(tmp_path / "report.md"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Invalid JSON" in captured.err
    assert "Traceback" not in captured.err


def test_missing_json_input_produces_controlled_failure(tmp_path, capsys):
    generator = load_generator()
    candidate_path = tmp_path / "candidate.json"
    manifest_path = tmp_path / "manifest.yaml"
    write_output(candidate_path, "onnx_candidate", [fixture_result("a", ["pop"])])
    manifest_path.write_text('schema_version: "0.1"\n', encoding="utf-8")

    exit_code = generator.main(
        [
            "--baseline-output",
            str(tmp_path / "missing.json"),
            "--candidate-output",
            str(candidate_path),
            "--manifest",
            str(manifest_path),
            "--output-report",
            str(tmp_path / "report.md"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unable to read JSON input" in captured.err
    assert "Traceback" not in captured.err


def test_generator_source_stays_offline_and_dependency_free():
    text = GENERATOR_PATH.read_text(encoding="utf-8")

    forbidden = (
        "onnxruntime",
        "tensorflow",
        "essentia",
        "requests",
        "urllib",
        "app.services",
        "providers",
        "provider_factory",
        "subprocess",
        "socket",
    )
    for token in forbidden:
        assert token not in text
