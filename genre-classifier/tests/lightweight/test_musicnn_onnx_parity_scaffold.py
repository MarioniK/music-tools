import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_onnx_parity_scaffold.py"
EVIDENCE_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json"
)
FALSE_RUNTIME_FLAGS = (
    "inference_attempted",
    "onnxruntime_imported",
    "tensorflow_imported",
    "essentia_imported",
    "classify_called",
    "provider_imported",
    "production_runtime_touched",
)

FORBIDDEN_CLAIMS = (
    "parity proven",
    "model parity proven",
    "production ready",
    "replacement approved",
    "onnx replacement approved",
    "provider switch approved",
)


def load_scaffold():
    spec = importlib.util.spec_from_file_location("musicnn_onnx_parity_scaffold", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_scaffold(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=SERVICE_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in result.stderr
    assert "Traceback" not in result.stdout
    return result, json.loads(result.stdout)


def load_evidence_payload():
    return json.loads(EVIDENCE_REPORT_PATH.read_text(encoding="utf-8"))


def write_report(tmp_path, payload):
    path = tmp_path / "evidence-report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def artifact_by_role(payload, role):
    for artifact in payload["artifacts"]:
        if artifact["artifact_role"] == role:
            return artifact
    raise AssertionError(f"missing artifact role in fixture: {role}")


def assert_runtime_flags_false(output):
    for flag in FALSE_RUNTIME_FLAGS:
        assert output[flag] is False


def assert_no_forbidden_claims(output):
    serialized = json.dumps(output).casefold()
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in serialized


def test_default_parity_spike_writes_safe_report(tmp_path):
    report_path = tmp_path / "musicnn-onnx-parity-spike-report.json"
    result, output = run_scaffold("--report", str(report_path))

    assert result.returncode == 0
    assert output["roadmap"] == "4.40"
    assert output["report_type"] == "musicnn_onnx_parity_spike_report"
    assert output["not_production_decision"] is True
    assert output["approved_for_production"] is False
    assert output["approved_for_provider_implementation"] is False
    assert output["approved_for_default_provider_switch"] is False
    assert output["onnxruntime_added_to_production_requirements"] is False
    assert output["approved_for_inference_beyond_local_spike"] is False
    assert output["no_classify_calls"] is True
    assert output["baseline_capture_attempted"] is False
    assert output["onnx_capture_attempted"] is False
    assert set(output["metrics"]) >= {
        "fixture_count",
        "baseline_runtime_available",
        "onnx_runtime_available",
        "max_abs_diff",
        "mean_abs_diff",
        "top_1_match",
        "top_3_overlap",
        "top_5_overlap",
        "preprocessing_alignment_status",
    }
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == output
    assert_no_forbidden_claims(output)


def test_explicit_parity_spike_succeeds(tmp_path):
    report_path = tmp_path / "musicnn-onnx-parity-spike-report.json"
    result, output = run_scaffold("--mode", "parity-spike", "--report", str(report_path))

    assert result.returncode == 0
    assert output["roadmap"] == "4.40"
    assert output["report_type"] == "musicnn_onnx_parity_spike_report"
    assert_no_forbidden_claims(output)


def test_explicit_dry_run_succeeds():
    result, output = run_scaffold("--mode", "dry-run")

    assert result.returncode == 0
    assert output["ok"] is True
    assert output["mode"] == "dry-run"
    assert_runtime_flags_false(output)


def test_explicit_evidence_report_path_succeeds():
    result, output = run_scaffold("--mode", "dry-run", "--evidence-report", str(EVIDENCE_REPORT_PATH))

    assert result.returncode == 0
    assert output["ok"] is True
    assert output["evidence_report_path"] == str(EVIDENCE_REPORT_PATH)
    assert_runtime_flags_false(output)


def test_invalid_report_path_returns_json_without_traceback(tmp_path):
    missing_path = tmp_path / "missing-report.json"

    result, output = run_scaffold("--mode", "dry-run", "--evidence-report", str(missing_path))

    assert result.returncode != 0
    assert output["ok"] is False
    assert_runtime_flags_false(output)
    assert any("not found" in item for item in output["no_go_items"])


def test_missing_required_role_fails(tmp_path):
    payload = load_evidence_payload()
    payload["artifacts"] = [
        artifact for artifact in payload["artifacts"] if artifact["artifact_role"] != "official_local_json"
    ]
    report_path = write_report(tmp_path, payload)

    scaffold = load_scaffold()
    output = scaffold.run_dry_run(report_path)

    assert output["ok"] is False
    assert_runtime_flags_false(output)
    assert any("official_local_json" in item for item in output["no_go_items"])


def test_approved_for_inference_true_fails(tmp_path):
    payload = load_evidence_payload()
    payload["approved_for_inference"] = True
    report_path = write_report(tmp_path, payload)

    scaffold = load_scaffold()
    output = scaffold.run_dry_run(report_path)

    assert output["ok"] is False
    assert any("approved_for_inference" in item for item in output["no_go_items"])


def test_approved_for_production_true_fails(tmp_path):
    payload = load_evidence_payload()
    payload["approved_for_production"] = True
    report_path = write_report(tmp_path, payload)

    scaffold = load_scaffold()
    output = scaffold.run_dry_run(report_path)

    assert output["ok"] is False
    assert any("approved_for_production" in item for item in output["no_go_items"])


def test_hash_mismatch_fails(tmp_path):
    payload = load_evidence_payload()
    artifact_by_role(payload, "official_local_onnx")["sha256"] = "0" * 64
    report_path = write_report(tmp_path, payload)

    scaffold = load_scaffold()
    output = scaffold.run_dry_run(report_path)

    assert output["ok"] is False
    assert any("Roadmap 4.30" in item for item in output["no_go_items"])


def test_output_does_not_claim_parity():
    _, output = run_scaffold("--mode", "dry-run")

    assert_no_forbidden_claims(output)


def test_mutating_fixture_does_not_change_source_payload():
    payload = load_evidence_payload()
    clone = copy.deepcopy(payload)
    artifact_by_role(clone, "official_local_onnx")["file_size_bytes"] = 1

    assert artifact_by_role(payload, "official_local_onnx")["file_size_bytes"] == 3168334
