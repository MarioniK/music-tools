import importlib.util
import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = SERVICE_ROOT / "scripts/lightweight/onnx_candidate_spike.py"


def load_spike_script():
    spec = importlib.util.spec_from_file_location("onnx_candidate_spike", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def assert_classify_compatible_shape(value):
    assert isinstance(value["ok"], bool)
    assert isinstance(value["message"], str)
    assert isinstance(value["genres"], list)
    assert isinstance(value["genres_pretty"], list)
    assert all(isinstance(item, str) for item in value["genres_pretty"])

    for item in value["genres"]:
        assert isinstance(item, dict)
        assert isinstance(item["tag"], str)
        assert isinstance(item["prob"], (int, float))


def run_spike(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stderr == ""
    return json.loads(result.stdout)


def assert_spike_metadata_shape(value):
    assert value["spike"]["roadmap"] == "4.8"
    assert value["spike"]["variant"] == "B"
    assert value["spike"]["mode"] == "dry_run"
    assert value["spike"]["inference_executed"] is False
    assert value["spike"]["audio_processed"] is False
    assert value["runtime"]["package"] == "onnxruntime"
    assert isinstance(value["runtime"]["available"], bool)
    assert value["runtime"]["imported"] is False
    assert value["runtime"]["detection_method"] == 'importlib.util.find_spec("onnxruntime")'
    assert isinstance(value["resource_latency_metadata"]["started_at_utc"], str)
    assert isinstance(value["resource_latency_metadata"]["finished_at_utc"], str)
    assert isinstance(value["resource_latency_metadata"]["duration_ms"], (int, float))
    assert isinstance(value["resource_latency_metadata"]["python_version"], str)
    assert isinstance(value["resource_latency_metadata"]["platform"], str)
    assert isinstance(value["warnings"], list)


def assert_smoke_metadata_shape(value):
    assert value["spike"]["roadmap"] == "4.10"
    assert value["spike"]["variant"] == "local_smoke"
    assert value["spike"]["mode"] == "smoke"
    assert value["metadata"]["mode"] == "smoke"
    assert value["metadata"]["candidate_provider"] == "onnx_local_smoke"
    assert value["metadata"]["provider"] == "onnx_local_smoke"
    assert value["metadata"]["baseline_provider"] == "legacy_musicnn"
    assert isinstance(value["metadata"]["onnxruntime_available"], bool)
    assert isinstance(value["metadata"]["provenance_approved"], bool)
    assert isinstance(value["metadata"]["label_mapping_approved"], bool)
    assert "label_mapping_path" in value["metadata"]
    assert "label_mapping_model_id" in value["metadata"]
    assert "label_mapping_label_count" in value["metadata"]
    assert isinstance(value["metadata"]["model_loaded"], bool)
    assert isinstance(value["metadata"]["inference_attempted"], bool)
    assert isinstance(value["metadata"]["inference_succeeded"], bool)
    assert isinstance(value["metadata"]["input_names"], list)
    assert isinstance(value["metadata"]["input_shapes"], list)
    assert isinstance(value["metadata"]["output_names"], list)
    assert isinstance(value["metadata"]["output_shapes"], list)
    assert "raw_score_count" in value["metadata"]
    assert isinstance(value["metadata"]["mapped_genre_count"], int)
    assert isinstance(value["metadata"]["warnings"], list)
    assert value["runtime"]["package"] == "onnxruntime"
    assert value["runtime"]["detection_method"] == 'importlib.util.find_spec("onnxruntime")'


def warning_categories(value):
    return {warning["category"] for warning in value["warnings"]}


def write_approved_provenance(path, model_path):
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    payload = {
        "schema_version": "0.1",
        "model_id": "local_smoke_test_model",
        "model_name": "Local Smoke Test Model",
        "model_family": "test_audio_genre_classifier",
        "model_format": "onnx",
        "source_url": "local-only:test",
        "source_repository": "local-only:test",
        "license": "Test-Only",
        "license_url": "local-only:test",
        "model_version": "test",
        "model_hash_sha256": digest,
        "model_file_name": model_path.name,
        "model_file_size_bytes": model_path.stat().st_size,
        "input_names": ["audio_input"],
        "input_shapes": [[1, 2]],
        "output_names": ["genre_scores"],
        "output_shapes": [[1, 2]],
        "label_source": "missing",
        "label_count": 0,
        "label_mapping_strategy": "missing",
        "intended_use": "local smoke test only",
        "known_limitations": ["no label mapping"],
        "approval_status": "approved",
        "warnings": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def write_label_mapping(
    path,
    *,
    model_id="local_smoke_test_model",
    approval_status="approved_for_offline_evaluation",
    labels=None,
):
    if labels is None:
        labels = [
            {
                "raw_label": "rock",
                "raw_index": 0,
                "mapped_genre": "rock",
                "mapped_confidence": "direct",
                "mapping_decision": "mapped",
                "mapping_notes": "test-only direct mapping",
            },
            {
                "raw_label": "hip hop",
                "raw_index": 1,
                "mapped_genre": "rap",
                "mapped_confidence": "review_required",
                "mapping_decision": "alias_mapped",
                "mapping_notes": "test-only alias mapping",
            },
            {
                "raw_label": "speech",
                "raw_index": 2,
                "mapped_genre": "",
                "mapped_confidence": "not_applicable",
                "mapping_decision": "ignored_non_genre",
                "mapping_notes": "test-only non-genre label",
            },
            {
                "raw_label": "unknown_tag",
                "raw_index": 3,
                "mapped_genre": "",
                "mapped_confidence": "none",
                "mapping_decision": "unmapped",
                "mapping_notes": "test-only unmapped label",
            },
            {
                "raw_label": "alternative",
                "raw_index": 4,
                "mapped_genre": "",
                "mapped_confidence": "rejected",
                "mapping_decision": "rejected_ambiguous",
                "mapping_notes": "test-only ambiguous label",
            },
            {
                "raw_label": "electronic",
                "raw_index": 5,
                "mapped_genre": "electronic",
                "mapped_confidence": "direct",
                "mapping_decision": "mapped",
                "mapping_notes": "test-only direct mapping",
            },
        ]
    payload = {
        "schema_version": "0.1",
        "mapping_id": "test_mapping",
        "model_id": model_id,
        "model_family": "test_audio_genre_classifier",
        "label_source": "test-only",
        "label_source_url": "test-only",
        "label_count": len(labels),
        "mapping_status": "test-only",
        "labels": labels,
        "controlled_vocabulary_version": "test-only",
        "unmapped_labels": [],
        "warnings": [],
        "approval_status": approval_status,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def build_mocked_smoke_output(monkeypatch, tmp_path, raw_outputs, *, label_mapping_payload=None):
    spike_script = load_spike_script()
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, model_path)
    mapping_path = tmp_path / "mapping.json"
    if label_mapping_payload is None:
        write_label_mapping(mapping_path)
    else:
        mapping_path.write_text(json.dumps(label_mapping_payload), encoding="utf-8")

    args = spike_script.build_parser().parse_args(
        [
            "--mode",
            "smoke",
            "--model-path",
            str(model_path),
            "--provenance-path",
            str(provenance_path),
            "--label-mapping-path",
            str(mapping_path),
        ]
    )

    class FakeValue:
        def __init__(self, name, shape, value_type="tensor(float)"):
            self.name = name
            self.shape = shape
            self.type = value_type

    class FakeSession:
        def __init__(self, path):
            self.path = path

        def get_inputs(self):
            return [FakeValue("audio_input", [1, 2])]

        def get_outputs(self):
            return [FakeValue("genre_scores", [1, 6])]

        def run(self, output_names, inputs):
            assert output_names is None
            assert "audio_input" in inputs
            return raw_outputs

    fake_runtime = types.SimpleNamespace(InferenceSession=FakeSession)
    monkeypatch.setattr(
        spike_script.importlib.util,
        "find_spec",
        lambda name: object() if name == "onnxruntime" else None,
    )
    monkeypatch.setattr(
        spike_script.importlib,
        "import_module",
        lambda name: fake_runtime if name == "onnxruntime" else importlib.import_module(name),
    )
    monkeypatch.setattr(spike_script, "_safe_dummy_input", lambda shape, input_type: object())

    return spike_script.build_smoke_output(args)


def test_dry_run_without_args_succeeds_without_heavy_dependencies():
    value = run_spike()

    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)
    assert value["spike"]["status"] == "dry_run_metadata_only"
    assert "no runtime loaded" in value["message"]
    assert "no model loaded for inference" in value["message"]
    assert "no audio processed" in value["message"]
    assert "no inference executed" in value["message"]
    assert value["model"]["path_provided"] is False
    assert value["model"]["size_bytes"] is None
    assert {"model_path_missing", "license_unknown", "model_provenance_unknown"} <= (
        warning_categories(value)
    )


def test_write_output_creates_valid_classify_compatible_json(tmp_path):
    output_path = tmp_path / "nested/output.json"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--write-output", str(output_path)],
        cwd=SERVICE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    value = json.loads(output_path.read_text(encoding="utf-8"))
    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)
    assert value["genres"] == [{"tag": "electronic", "prob": 0.0}]
    assert value["genres_pretty"] == ["Electronic"]


def test_output_alias_creates_structured_json(tmp_path):
    output_path = tmp_path / "artifact.json"

    value = run_spike("--output", str(output_path))

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == value
    assert_classify_compatible_shape(written)
    assert_spike_metadata_shape(written)


def test_script_builds_classify_compatible_payload():
    spike_script = load_spike_script()

    value = spike_script.build_dry_run_output()

    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)


def test_runtime_detection_does_not_require_runtime_import():
    spike_script = load_spike_script()

    value = spike_script.detect_onnxruntime()

    assert value["package"] == "onnxruntime"
    assert isinstance(value["available"], bool)
    assert value["imported"] is False
    assert value["detection_method"] == 'importlib.util.find_spec("onnxruntime")'


def test_missing_model_path_produces_controlled_status_and_warning(tmp_path):
    missing_path = tmp_path / "missing.onnx"

    value = run_spike("--model-path", str(missing_path))

    assert value["spike"]["status"] == "skipped_model_path_not_found"
    assert value["model"]["path_provided"] is True
    assert value["model"]["exists"] is False
    assert value["model"]["is_file"] is False
    assert value["model"]["suffix"] == ".onnx"
    assert value["model"]["size_bytes"] is None
    assert "model_path_not_found" in warning_categories(value)
    assert "model_suffix_not_onnx" not in warning_categories(value)


def test_no_model_path_keeps_metadata_only_dry_run_mode():
    value = run_spike("--dry-run")

    assert value["spike"]["status"] == "dry_run_metadata_only"
    assert value["model"] == {
        "path_provided": False,
        "path": None,
        "exists": None,
        "is_file": None,
        "suffix": None,
        "suffix_expected": ".onnx",
        "size_bytes": None,
    }
    assert value["resource_latency_metadata"]["model_size_bytes"] is None


def test_explicit_dry_run_mode_keeps_default_behavior():
    value = run_spike("--mode", "dry-run")

    assert_classify_compatible_shape(value)
    assert_spike_metadata_shape(value)
    assert value["spike"]["status"] == "dry_run_metadata_only"
    assert value["genres"] == [{"tag": "electronic", "prob": 0.0}]
    assert value["genres_pretty"] == ["Electronic"]


def test_temporary_fake_onnx_file_can_be_inspected_without_real_runtime(tmp_path):
    model_path = tmp_path / "fake.onnx"
    model_path.write_bytes(b"not a real model")

    value = run_spike("--model-path", str(model_path))

    assert value["spike"]["status"] == "local_model_inspected_no_inference"
    assert value["model"]["path_provided"] is True
    assert value["model"]["path"] == str(model_path)
    assert value["model"]["exists"] is True
    assert value["model"]["is_file"] is True
    assert value["model"]["suffix"] == ".onnx"
    assert value["model"]["size_bytes"] == len(b"not a real model")
    assert value["resource_latency_metadata"]["model_size_bytes"] == len(b"not a real model")
    assert value["spike"]["inference_executed"] is False
    assert "model_suffix_not_onnx" not in warning_categories(value)


def test_model_provenance_fields_are_recorded():
    value = run_spike(
        "--model-name",
        "example-audio-onnx",
        "--model-source-url",
        "https://example.invalid/model",
        "--license",
        "Example-License",
        "--license-url",
        "https://example.invalid/license",
        "--checksum-sha256",
        "0" * 64,
        "--provenance-status",
        "recorded",
    )

    assert value["provenance"] == {
        "model_name": "example-audio-onnx",
        "model_source_url": "https://example.invalid/model",
        "license": "Example-License",
        "license_url": "https://example.invalid/license",
        "checksum_sha256": "0" * 64,
        "provenance_status": "recorded",
    }
    assert "license_unknown" not in warning_categories(value)
    assert "model_provenance_unknown" not in warning_categories(value)


def test_smoke_mode_without_required_paths_returns_controlled_no_go():
    value = run_spike("--mode", "smoke")

    assert_classify_compatible_shape(value)
    assert_smoke_metadata_shape(value)
    assert value["ok"] is False
    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert value["metadata"]["model_loaded"] is False
    assert value["metadata"]["inference_attempted"] is False
    assert "provenance_path_missing" in warning_categories(value)
    assert "not_production_classification" in warning_categories(value)


def test_smoke_not_approved_provenance_blocks_before_model_loading():
    value = run_spike(
        "--mode",
        "smoke",
        "--model-path",
        "/tmp/nonexistent-model.onnx",
        "--provenance-path",
        "docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json",
    )

    assert_smoke_metadata_shape(value)
    assert value["ok"] is False
    assert value["metadata"]["provenance_approved"] is False
    assert value["metadata"]["model_loaded"] is False
    assert value["metadata"]["inference_attempted"] is False
    categories = warning_categories(value)
    assert "provenance_not_approved" in categories
    assert "model_path_missing" not in categories
    assert "model_path_not_file" not in categories


def test_smoke_approved_provenance_missing_model_is_controlled(tmp_path):
    model_path = tmp_path / "model.onnx"
    existing_model = tmp_path / "existing.onnx"
    existing_model.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, existing_model)

    value = run_spike(
        "--mode",
        "smoke",
        "--model-path",
        str(model_path),
        "--provenance-path",
        str(provenance_path),
    )

    assert value["ok"] is False
    assert value["metadata"]["provenance_approved"] is True
    assert value["metadata"]["model_loaded"] is False
    assert "model_path_missing" in warning_categories(value)


def test_smoke_missing_onnxruntime_returns_controlled_skip(monkeypatch, tmp_path):
    spike_script = load_spike_script()
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, model_path)
    args = spike_script.build_parser().parse_args(
        [
            "--mode",
            "smoke",
            "--model-path",
            str(model_path),
            "--provenance-path",
            str(provenance_path),
        ]
    )
    monkeypatch.setattr(spike_script.importlib.util, "find_spec", lambda name: None)

    value = spike_script.build_smoke_output(args)

    assert value["ok"] is False
    assert_smoke_metadata_shape(value)
    assert value["metadata"]["onnxruntime_available"] is False
    assert value["metadata"]["model_loaded"] is False
    assert "onnxruntime_missing" in warning_categories(value)


def test_label_mapping_path_is_optional_for_smoke(monkeypatch, tmp_path):
    spike_script = load_spike_script()
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, model_path)
    args = spike_script.build_parser().parse_args(
        [
            "--mode",
            "smoke",
            "--model-path",
            str(model_path),
            "--provenance-path",
            str(provenance_path),
        ]
    )
    monkeypatch.setattr(spike_script.importlib.util, "find_spec", lambda name: None)

    value = spike_script.build_smoke_output(args)

    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert value["metadata"]["label_mapping_path"] is None
    assert value["metadata"]["label_mapping_approved"] is False
    assert "label_mapping_missing" in warning_categories(value)


def test_not_approved_mapping_does_not_produce_genres(monkeypatch, tmp_path):
    mapping_payload = write_label_mapping(
        tmp_path / "not-approved-source.json",
        approval_status="not_approved",
    )

    value = build_mocked_smoke_output(
        monkeypatch,
        tmp_path,
        [[0.91, 0.82, 0.7, 0.6, 0.5, 0.41]],
        label_mapping_payload=mapping_payload,
    )

    assert value["ok"] is True
    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert value["metadata"]["label_mapping_approved"] is False
    assert value["metadata"]["raw_score_count"] == 6
    assert "label_mapping_not_approved" in warning_categories(value)


def test_approved_mapping_can_produce_genres_from_static_test_only_raw_scores(
    monkeypatch, tmp_path
):
    value = build_mocked_smoke_output(
        monkeypatch,
        tmp_path,
        [[0.91, 0.82, 0.7, 0.6, 0.5, 0.41]],
    )

    assert value["ok"] is True
    assert_classify_compatible_shape(value)
    assert value["genres"] == [
        {"tag": "rock", "prob": 0.91},
        {"tag": "rap", "prob": 0.82},
        {"tag": "electronic", "prob": 0.41},
    ]
    assert value["genres_pretty"] == ["Rock", "Rap", "Electronic"]
    assert value["metadata"]["label_mapping_approved"] is True
    assert value["metadata"]["raw_score_count"] == 6
    assert value["metadata"]["mapped_genre_count"] == 3


def test_only_mapped_and_alias_mapped_entries_produce_genres(monkeypatch, tmp_path):
    value = build_mocked_smoke_output(
        monkeypatch,
        tmp_path,
        [[0.91, 0.82, 0.7, 0.6, 0.5, 0.41]],
    )

    assert [item["tag"] for item in value["genres"]] == ["rock", "rap", "electronic"]
    assert "speech" not in value["genres_pretty"]
    assert "unknown_tag" not in [item["tag"] for item in value["genres"]]
    assert "alternative" not in [item["tag"] for item in value["genres"]]


def test_model_id_mismatch_blocks_genre_mapping(monkeypatch, tmp_path):
    mapping_payload = write_label_mapping(
        tmp_path / "mismatch-source.json",
        model_id="different_model",
    )

    value = build_mocked_smoke_output(
        monkeypatch,
        tmp_path,
        [[0.91, 0.82, 0.7, 0.6, 0.5, 0.41]],
        label_mapping_payload=mapping_payload,
    )

    assert value["genres"] == []
    assert value["metadata"]["label_mapping_approved"] is False
    assert "label_mapping_model_id_mismatch" in warning_categories(value)


def test_raw_score_count_mismatch_blocks_genre_mapping(monkeypatch, tmp_path):
    value = build_mocked_smoke_output(
        monkeypatch,
        tmp_path,
        [[0.91, 0.82]],
    )

    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert value["metadata"]["label_mapping_approved"] is True
    assert value["metadata"]["raw_score_count"] == 2
    assert "raw_score_label_count_mismatch" in warning_categories(value)


def test_missing_raw_scores_do_not_create_fake_probabilities(monkeypatch, tmp_path):
    class FakeOutput:
        shape = [1, 6]

    value = build_mocked_smoke_output(monkeypatch, tmp_path, [FakeOutput()])

    assert value["ok"] is True
    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert value["metadata"]["raw_output_shape"] == [1, 6]
    assert value["metadata"]["raw_score_count"] is None
    assert value["metadata"]["mapped_genre_count"] == 0
    assert "raw_scores_missing" in warning_categories(value)


def test_smoke_output_path_refuses_overwrite(tmp_path):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, model_path)
    output_path = tmp_path / "smoke.json"
    output_path.write_text("existing\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--mode",
            "smoke",
            "--model-path",
            str(model_path),
            "--provenance-path",
            str(provenance_path),
            "--output-path",
            str(output_path),
        ],
        cwd=SERVICE_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "output write refused" in result.stderr
    assert output_path.read_text(encoding="utf-8") == "existing\n"


def test_smoke_output_path_writes_when_requested(tmp_path):
    output_path = tmp_path / "nested/smoke.json"

    value = run_spike(
        "--mode",
        "smoke",
        "--model-path",
        "/tmp/nonexistent-model.onnx",
        "--provenance-path",
        "docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json",
        "--output-path",
        str(output_path),
    )

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == value
    assert_smoke_metadata_shape(written)


def test_mocked_successful_smoke_path_records_raw_output_metadata(monkeypatch, tmp_path):
    spike_script = load_spike_script()
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake local model")
    provenance_path = tmp_path / "provenance.json"
    write_approved_provenance(provenance_path, model_path)
    args = spike_script.build_parser().parse_args(
        [
            "--mode",
            "smoke",
            "--model-path",
            str(model_path),
            "--provenance-path",
            str(provenance_path),
        ]
    )

    class FakeValue:
        def __init__(self, name, shape, value_type="tensor(float)"):
            self.name = name
            self.shape = shape
            self.type = value_type

    class FakeOutput:
        shape = [1, 2]

    class FakeSession:
        def __init__(self, path):
            self.path = path

        def get_inputs(self):
            return [FakeValue("audio_input", [1, 2])]

        def get_outputs(self):
            return [FakeValue("genre_scores", [1, 2])]

        def run(self, output_names, inputs):
            assert output_names is None
            assert "audio_input" in inputs
            return [FakeOutput()]

    fake_runtime = types.SimpleNamespace(InferenceSession=FakeSession)
    monkeypatch.setattr(
        spike_script.importlib.util,
        "find_spec",
        lambda name: object() if name == "onnxruntime" else None,
    )
    monkeypatch.setattr(
        spike_script.importlib,
        "import_module",
        lambda name: fake_runtime if name == "onnxruntime" else importlib.import_module(name),
    )
    monkeypatch.setattr(spike_script, "_safe_dummy_input", lambda shape, input_type: object())

    value = spike_script.build_smoke_output(args)

    assert value["ok"] is True
    assert value["metadata"]["onnxruntime_available"] is True
    assert value["metadata"]["model_loaded"] is True
    assert value["metadata"]["inference_attempted"] is True
    assert value["metadata"]["inference_succeeded"] is True
    assert value["metadata"]["input_names"] == ["audio_input"]
    assert value["metadata"]["output_names"] == ["genre_scores"]
    assert value["metadata"]["raw_output_shape"] == [1, 2]
    assert value["genres"] == []
    assert value["genres_pretty"] == []
    assert "label_mapping_missing" in warning_categories(value)
    assert "not_production_classification" in warning_categories(value)


def test_script_source_does_not_import_heavy_runtime_modules():
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    forbidden_markers = (
        "import onnxruntime",
        "from onnxruntime",
        "import tensorflow",
        "from tensorflow",
        "import essentia",
        "from essentia",
        "import app.main",
        "from app.main",
        "provider_factory",
    )

    for marker in forbidden_markers:
        assert marker not in source
