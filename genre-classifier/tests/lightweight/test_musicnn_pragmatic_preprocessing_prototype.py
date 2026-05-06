import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


SERVICE_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py"


def load_helper():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("musicnn_pragmatic_preprocessing_prototype", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    imported = set(sys.modules) - before
    return module, imported


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
    assert "metadata-only" in result.stdout
    assert "preprocessing-probe" in result.stdout


def _stub_args(mode: str, report_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        mode=mode,
        agents_md_read=True,
        baseline_report=Path("baseline.json"),
        fixtures_dir=Path("fixtures"),
        onnx_model=Path("msd-musicnn-1.onnx"),
        onnx_metadata=Path("msd-musicnn-1.json"),
        python=Path("python"),
        report=report_path,
    )


def _stub_baseline():
    return {
        "report_path": "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
        "available": True,
        "fixture_count": 3,
        "fixture_ids": [
            "john_bartmann_earning_happiness_cc0",
            "john_bartmann_happy_clappy_cc0",
            "john_bartmann_home_at_last_cc0",
        ],
        "expected_output_shapes": [[30, 50], [35, 50], [86, 50]],
    }


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


def _stub_onnx_metadata():
    return {
        "available": True,
        "onnxruntime_available": True,
        "onnxruntime_version": "1.25.1",
        "model_sha256": "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1",
        "metadata_sha256": "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe",
        "input_name": "melspectrogram",
        "input_shape_tail": [187, 96],
        "output_names": ["activations", "embeddings"],
        "output_shape_tails": [[50], [200]],
    }


def _stub_essentia_probe(available: bool):
    if available:
        return {"available": True, "error": None, "algorithm_names": ["MelBands", "MonoLoader"]}
    return {"available": False, "error": "ModuleNotFoundError: No module named 'essentia'", "algorithm_names": []}


def test_metadata_only_report_is_sanitized_and_scoped(tmp_path):
    helper, _ = load_helper()
    helper._load_baseline_evidence = lambda path: _stub_baseline()
    helper._collect_fixture_records = lambda path: _stub_fixtures()
    helper._inspect_onnx_metadata = lambda model_path, metadata_path, python_executable: _stub_onnx_metadata()
    helper._probe_essentia_standard_runtime = lambda python_executable: _stub_essentia_probe(False)

    report = helper.build_report(_stub_args("metadata-only", tmp_path / "report.json"))
    serialized = json.dumps(report)

    assert report["report_type"] == "musicnn_onnx_pragmatic_preprocessing_prototype_report"
    assert report["prototype_modes"] == ["metadata_only", "preprocessing_probe"]
    assert report["onnx_input"]["input_name"] == "melspectrogram"
    assert report["onnx_input"]["shape_tail"] == [187, 96]
    assert report["preprocessing_probe_result"]["attempted"] is False
    assert report["preprocessing_probe_result"]["succeeded"] is False
    assert report["local_environment"]["essentia_available"] is False
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized


def test_preprocessing_probe_records_dependency_blockers_without_fake_outputs(tmp_path):
    helper, _ = load_helper()
    helper._load_baseline_evidence = lambda path: _stub_baseline()
    helper._collect_fixture_records = lambda path: _stub_fixtures()
    helper._inspect_onnx_metadata = lambda model_path, metadata_path, python_executable: _stub_onnx_metadata()
    helper._probe_essentia_standard_runtime = lambda python_executable: _stub_essentia_probe(False)

    report = helper.build_report(_stub_args("preprocessing-probe", tmp_path / "report.json"))
    blocker_codes = {item["code"] for item in report["blockers"]}

    assert report["preprocessing_probe_result"]["attempted"] is True
    assert report["preprocessing_probe_result"]["succeeded"] is False
    assert report["preprocessing_probe_result"]["produced_shape"] is None
    assert report["preprocessing_probe_result"]["repeated_run_stability_checked"] is False
    assert blocker_codes >= {
        "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
        "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
    }
