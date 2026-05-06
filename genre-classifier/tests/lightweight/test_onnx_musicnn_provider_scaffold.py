import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.providers.compat import (
    map_validated_result_to_legacy_genres,
    map_validated_result_to_legacy_genres_pretty,
)
from app.providers.onnx_musicnn import (
    OnnxMusiCNNProvider,
    build_candidate_scores,
)
from app.providers.schema import ValidatedProviderResult
from app.providers.validation import validate_and_normalize_provider_result


SERVICE_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = SERVICE_ROOT / "app" / "providers" / "onnx_musicnn.py"


def test_provider_module_import_does_not_require_onnxruntime_or_essentia():
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("onnx_musicnn_scaffold_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    imported = set(sys.modules) - before

    assert "onnxruntime" not in imported
    assert "essentia" not in imported
    assert "essentia.standard" not in imported
    assert module.ONNX_MUSICNN_PROVIDER_NAME == "onnx_musicnn"


def test_build_candidate_scores_preserves_index_alignment_and_top_n_order():
    scores = build_candidate_scores(
        [0.72, 0.91, 0.91, 0.5],
        ["dream-pop", "indie rock", "ambient", "post punk"],
        top_n=3,
    )

    assert [(item.tag, item.score) for item in scores] == [
        ("indie rock", 0.91),
        ("ambient", 0.91),
        ("dream pop", 0.72),
    ]


def test_build_candidate_scores_maps_aliases_and_keeps_unknown_labels_safe():
    scores = build_candidate_scores(
        [0.9, 0.8, 0.7],
        ["dream-pop", "space yacht metal", "ambient"],
    )

    assert [(item.tag, item.score) for item in scores] == [
        ("dream pop", 0.9),
        ("space yacht metal", 0.8),
        ("ambient", 0.7),
    ]


@pytest.mark.parametrize(
    "activations, classes, expected_message",
    [
        (None, ["dream pop"], "invalid activations"),
        ([0.9], [], "empty classes"),
        ([0.9, 0.8], ["dream pop"], "activations/classes count mismatch"),
        ([[0.9, 0.8]], ["dream pop", "ambient"], "invalid activations shape"),
    ],
)
def test_build_candidate_scores_rejects_invalid_inputs(activations, classes, expected_message):
    with pytest.raises(RuntimeError, match=expected_message):
        build_candidate_scores(activations, classes)


def test_provider_runtime_status_reports_missing_artifacts_without_crashing(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    metadata_path = model_dir / "msd-musicnn-1.json"
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "model artifact missing: msd-musicnn-1.onnx" in status["reasons"]


def test_provider_runtime_status_reports_missing_metadata_without_crashing(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "msd-musicnn-1.onnx").write_bytes(b"stub model")

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "metadata artifact missing: msd-musicnn-1.json" in status["reasons"]


def test_provider_runtime_status_reports_missing_dependency_without_crashing(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "msd-musicnn-1.onnx").write_bytes(b"stub model")
    (model_dir / "msd-musicnn-1.json").write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: (_ for _ in ()).throw(RuntimeError("onnxruntime unavailable")))
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnxruntime unavailable" in status["reasons"]


def test_provider_runtime_status_reports_missing_tensorflow_input_musiccnn_boundary(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "msd-musicnn-1.onnx").write_bytes(b"stub model")
    (model_dir / "msd-musicnn-1.json").write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: (_ for _ in ()).throw(RuntimeError("TensorflowInputMusiCNN unavailable")),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "TensorflowInputMusiCNN unavailable" in status["reasons"]


def test_provider_classify_reports_disabled_scaffold_state(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "msd-musicnn-1.onnx").write_bytes(b"stub model")
    (model_dir / "msd-musicnn-1.json").write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    with pytest.raises(RuntimeError, match="disabled-by-default"):
        provider.classify("/tmp/audio.wav")


def test_provider_classify_reports_missing_onnxruntime_as_controlled_failure(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "msd-musicnn-1.onnx").write_bytes(b"stub model")
    (model_dir / "msd-musicnn-1.json").write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=model_dir),
    )
    monkeypatch.setattr(
        provider,
        "_load_onnxruntime",
        lambda: (_ for _ in ()).throw(RuntimeError("onnxruntime unavailable")),
    )
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    with pytest.raises(RuntimeError, match="onnxruntime unavailable"):
        provider.classify("/tmp/audio.wav")


def test_valid_mapping_result_is_compatible_with_existing_genres_contract():
    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(MODELS_DIR=Path("/does/not/matter")),
    )
    provider_result = provider.build_provider_result_from_outputs(
        [0.93, 0.84, 0.6],
        ["dream-pop", "space yacht metal", "ambient"],
        model_name="onnx-musicnn-test",
    )

    validated_result = validate_and_normalize_provider_result(provider_result)
    genres = map_validated_result_to_legacy_genres(validated_result)
    genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)

    assert isinstance(validated_result, ValidatedProviderResult)
    assert provider_result.provider_name == "onnx_musicnn"
    assert [item.tag for item in validated_result.genres] == [
        "dream pop",
        "space yacht metal",
        "ambient",
    ]
    assert genres == [
        {"tag": "dream pop", "prob": 0.93},
        {"tag": "space yacht metal", "prob": 0.84},
        {"tag": "ambient", "prob": 0.6},
    ]
    assert genres_pretty == ["dream pop", "space yacht metal", "ambient"]
