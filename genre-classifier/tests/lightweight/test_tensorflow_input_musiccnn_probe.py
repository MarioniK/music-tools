import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


SERVICE_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_tensorflow_input_probe.py"


def load_helper():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("musicnn_tensorflow_input_probe", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    imported = set(sys.modules) - before
    return module, imported


def _stub_args(mode: str, report_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        mode=mode,
        agents_md_read=True,
        fixtures_dir=Path("fixtures"),
        isolated_python=Path("python"),
        strategy_report=Path("roadmap-4.55.json"),
        prototype_report=Path("roadmap-4.56.json"),
        report=report_path,
    )


def _stub_fixtures():
    return [
        {
            "fixture_id": "john_bartmann_earning_happiness_cc0",
            "sha256": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
            "license_status": "CC0 1.0 Universal / public domain",
        },
        {
            "fixture_id": "john_bartmann_happy_clappy_cc0",
            "sha256": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
            "license_status": "CC0 1.0 Universal / public domain",
        },
        {
            "fixture_id": "john_bartmann_home_at_last_cc0",
            "sha256": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
            "license_status": "CC0 1.0 Universal / public domain",
        },
    ]


def _stub_strategy_report():
    return {
        "path": "docs/lightweight/evaluation/evidence/roadmap-4.55-onnx-musicnn-pragmatic-preprocessing-strategy-report.json",
        "exists": True,
        "roadmap": "4.55",
        "target_candidate": "official_onnx_musicnn",
        "not_production_decision": True,
    }


def _stub_prototype_report():
    return {
        "path": "docs/lightweight/evaluation/evidence/roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json",
        "exists": True,
        "roadmap": "4.56",
        "target_candidate": "official_onnx_musicnn",
        "not_production_decision": True,
    }


def _stub_onnxruntime(available: bool):
    if available:
        return {
            "available": True,
            "version": "1.25.1",
            "error_category": None,
            "error_message": None,
        }
    return {
        "available": False,
        "version": None,
        "error_category": "ModuleNotFoundError",
        "error_message": "No module named 'onnxruntime'",
    }


def _stub_python(available: bool):
    if available:
        return {
            "python_available": True,
            "import_status": "imported",
            "import_error_category": None,
            "import_error_message": None,
            "hasattr_result": True,
            "available": True,
        }
    return {
        "python_available": True,
        "import_status": "failed",
        "import_error_category": "ModuleNotFoundError",
        "import_error_message": "No module named 'essentia'",
        "hasattr_result": False,
        "available": False,
    }


def test_helper_import_is_lightweight_and_runtime_free():
    _, imported = load_helper()

    assert "tensorflow" not in imported
    assert "essentia" not in imported
    assert "onnx" not in imported
    assert "onnxruntime" not in imported
    assert "app" not in imported


def test_helper_help_mentions_modes():
    result = subprocess.run(
        [sys.executable, str(HELPER_PATH), "--help"],
        cwd=SERVICE_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "availability" in result.stdout
    assert "preprocessing-probe" in result.stdout


def test_availability_report_records_blockers_and_sanitized_paths(tmp_path, monkeypatch):
    helper, _ = load_helper()
    monkeypatch.setattr(
        helper,
        "_load_baseline_report",
        lambda path: _stub_strategy_report() if "4.55" in str(path) else _stub_prototype_report(),
    )
    monkeypatch.setattr(helper, "_collect_fixture_records", lambda path: _stub_fixtures())
    monkeypatch.setattr(helper, "_probe_onnxruntime_version", lambda path: _stub_onnxruntime(True))
    monkeypatch.setattr(helper, "_probe_python", lambda path: _stub_python(False))
    monkeypatch.setattr(helper.shutil, "which", lambda name: "/usr/bin/python3")

    report = helper.build_report(_stub_args("availability", tmp_path / "report.json"))
    serialized = json.dumps(report)

    assert report["report_type"] == "musicnn_tensorflow_input_musiccnn_availability_probe_report"
    assert report["isolated_python_used_for_availability_check"] is True
    assert report["preprocessing_probe_execution"] == "current_interpreter"
    assert "approved isolated Python interpreter" in report["recommended_isolated_probe_invocation"]
    assert "--mode preprocessing-probe" in report["recommended_isolated_probe_invocation"]
    assert report["tensorflow_input_musiccnn"]["available_in_isolated_env"] is False
    assert report["tensorflow_input_musiccnn"]["available_in_system_python"] is False
    assert report["preprocessing_probe_result"]["attempted"] is False
    assert report["preprocessing_probe_result"]["produced_shape"] is None
    assert report["fallback"]["generic_melbands_fallback_evaluated"] is True
    assert report["fallback"]["generic_melbands_fallback_used"] is False
    assert report["fallback"]["fallback_status"] == "blocked"
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized

    blocker_codes = {item["code"] for item in report["blockers"]}
    assert blocker_codes >= {
        "ESSENTIA_IMPORT_FAILED",
        "TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED",
        "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
        "GENERIC_MELBANDS_FALLBACK_BLOCKED",
    }


def test_preprocessing_probe_reports_successful_patch_shape_when_available(tmp_path, monkeypatch):
    helper, _ = load_helper()
    monkeypatch.setattr(
        helper,
        "_load_baseline_report",
        lambda path: _stub_strategy_report() if "4.55" in str(path) else _stub_prototype_report(),
    )
    monkeypatch.setattr(helper, "_collect_fixture_records", lambda path: _stub_fixtures())
    monkeypatch.setattr(helper, "_probe_onnxruntime_version", lambda path: _stub_onnxruntime(True))
    monkeypatch.setattr(helper, "_probe_python", lambda path: _stub_python(True))
    monkeypatch.setattr(helper, "_capture_tensorflow_input_patch", lambda **kwargs: {
        "fixture_id": kwargs["fixture_id"],
        "produced_shape": [187, 96],
        "patch_digest": "stable-digest",
    })
    monkeypatch.setattr(helper.shutil, "which", lambda name: "/usr/bin/python3")

    report = helper.build_report(_stub_args("preprocessing-probe", tmp_path / "report.json"))

    assert report["preprocessing_probe_result"]["attempted"] is True
    assert report["preprocessing_probe_result"]["succeeded"] is True
    assert report["preprocessing_probe_result"]["produced_shape"] == [187, 96]
    assert report["preprocessing_probe_result"]["repeated_run_stability_checked"] is True
    assert report["preprocessing_probe_result"]["stable"] is True
    assert report["isolated_python_used_for_availability_check"] is True
    assert report["preprocessing_probe_execution"] == "current_interpreter"
    assert "--mode preprocessing-probe" in report["recommended_isolated_probe_invocation"]
    assert report["blockers"] == []
