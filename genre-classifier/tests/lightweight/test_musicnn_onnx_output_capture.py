import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


SERVICE_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = SERVICE_ROOT / "scripts/lightweight/musicnn_onnx_output_capture.py"


def load_helper():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("musicnn_onnx_output_capture", HELPER_PATH)
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


def test_helper_records_blocked_preprocessing_alignment_without_fake_outputs():
    helper, _ = load_helper()

    monkey_args = SimpleNamespace(
        agents_md_read=True,
        baseline_report=Path("baseline.json"),
        fixtures_dir=Path("fixtures"),
        model_onnx=Path("msd-musicnn-1.onnx"),
        model_json=Path("msd-musicnn-1.json"),
        python=Path("python"),
        output=Path("report.json"),
    )

    helper._load_baseline_evidence = lambda path: {
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
    helper._collect_fixture_records = lambda path: (
        [
            {
                "fixture_id": "john_bartmann_earning_happiness_cc0",
                "sha256": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
                "audio_format": "mp3",
                "source_artist": "John Bartmann",
                "license_status": "CC0 1.0 Universal / public domain",
            },
            {
                "fixture_id": "john_bartmann_happy_clappy_cc0",
                "sha256": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
                "audio_format": "mp3",
                "source_artist": "John Bartmann",
                "license_status": "CC0 1.0 Universal / public domain",
            },
            {
                "fixture_id": "john_bartmann_home_at_last_cc0",
                "sha256": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
                "audio_format": "mp3",
                "source_artist": "John Bartmann",
                "license_status": "CC0 1.0 Universal / public domain",
            },
        ],
        [
            {"fixture_id": "john_bartmann_earning_happiness_cc0"},
            {"fixture_id": "john_bartmann_happy_clappy_cc0"},
            {"fixture_id": "john_bartmann_home_at_last_cc0"},
        ],
    )
    helper._inspect_onnx_metadata = lambda model_onnx, model_json, python_executable: {
        "available": True,
        "onnxruntime_available": True,
        "onnxruntime_version": "1.25.1",
        "model_sha256": "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1",
        "metadata_sha256": "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe",
        "artifact_in_repo": False,
        "input_names": ["melspectrogram"],
        "input_shapes": [["dyn", 187, 96]],
        "output_names": ["activations", "embeddings"],
        "output_shapes": [["dyn", 50], ["dyn", 200]],
        "preprocessing_alignment_status": "unknown",
    }

    payload = helper.build_report(monkey_args)
    serialized = helper.json.dumps(payload)

    assert payload["report_type"] == "musicnn_onnx_output_capture_report"
    assert payload["onnx_capture_succeeded"] is False
    assert payload["onnx_capture_status"]["blocked_preprocessing_unknown"] is True
    assert payload["onnx_outputs"] == []
    assert payload["blockers"][0]["code"] == "PREPROCESSING_ALIGNMENT_UNKNOWN"
    assert "/tmp/music-tools-onnx-parity" not in serialized
    assert "/opt/music-tools" not in serialized
