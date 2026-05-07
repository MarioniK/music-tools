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


def _build_provider(*, model_path=None, metadata_path=None):
    return OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(
            get_configured_onnx_musicnn_model_path=lambda: model_path,
            get_configured_onnx_musicnn_metadata_path=lambda: metadata_path,
        ),
    )


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


def test_provider_runtime_status_reports_unconfigured_artifacts_without_crashing(monkeypatch):
    provider = _build_provider()
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx model path not configured" in status["reasons"]
    assert "onnx metadata path not configured" in status["reasons"]


def test_provider_runtime_status_reports_missing_model_artifact_without_crashing(tmp_path, monkeypatch):
    provider = _build_provider(
        model_path=tmp_path / "msd-musicnn-1.onnx",
        metadata_path=tmp_path / "msd-musicnn-1.json",
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx model artifact missing" in status["reasons"]


def test_provider_runtime_status_reports_missing_metadata_artifact_without_crashing(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    model_path.write_bytes(b"stub model")
    provider = _build_provider(
        model_path=model_path,
        metadata_path=tmp_path / "msd-musicnn-1.json",
    )
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx metadata artifact missing" in status["reasons"]


def test_provider_runtime_status_accepts_explicit_artifact_paths(tmp_path, monkeypatch):
    model_path = tmp_path / "explicit-model.onnx"
    metadata_path = tmp_path / "explicit-metadata.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is True
    assert status["reasons"] == []
    assert status["model_path"] == str(model_path)
    assert status["metadata_path"] == str(metadata_path)


def test_provider_runtime_status_reports_missing_dependency_without_crashing(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
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
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: (_ for _ in ()).throw(RuntimeError("TensorflowInputMusiCNN unavailable")),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "TensorflowInputMusiCNN unavailable" in status["reasons"]


def test_provider_classify_uses_explicit_artifacts_for_opt_in_smoke(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    audio_path = tmp_path / "fixture.mp3"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )
    audio_path.write_bytes(b"stub audio")

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )
    monkeypatch.setattr(provider, "_build_tensorflow_input_patch", lambda *_: [[0.91, 0.73]])
    monkeypatch.setattr(provider, "_run_onnx_inference", lambda *_: [0.91, 0.73])

    provider_result = provider.classify(str(audio_path))

    assert provider_result.provider_name == "onnx_musicnn"
    assert provider_result.model_name == "onnx-musicnn-scaffold"
    assert [(item.tag, item.score) for item in provider_result.genres] == [
        ("dream pop", 0.91),
        ("ambient", 0.73),
    ]


def test_provider_classify_reports_missing_onnxruntime_as_controlled_failure(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
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


def test_provider_classify_with_explicit_artifacts_returns_provider_result(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    audio_path = tmp_path / "fixture.mp3"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient", "electronic"]}),
        encoding="utf-8",
    )
    audio_path.write_bytes(b"stub audio")

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )
    monkeypatch.setattr(provider, "_build_tensorflow_input_patch", lambda *_: [[0.93, 0.72, 0.41]])
    monkeypatch.setattr(provider, "_run_onnx_inference", lambda *_: [0.93, 0.72, 0.41])

    provider_result = provider.classify_with_explicit_artifacts(str(audio_path), top_n=2)

    assert provider_result.provider_name == "onnx_musicnn"
    assert provider_result.model_name == "onnx-musicnn-scaffold"
    assert [(item.tag, item.score) for item in provider_result.genres] == [
        ("dream pop", 0.93),
        ("ambient", 0.72),
    ]


def test_provider_classify_with_explicit_artifacts_reports_missing_audio_artifact(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(
        json.dumps({"classes": ["dream-pop", "ambient"]}),
        encoding="utf-8",
    )

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    with pytest.raises(RuntimeError, match="audio artifact missing"):
        provider.classify_with_explicit_artifacts(str(tmp_path / "missing.mp3"))


def test_provider_runtime_status_reports_invalid_metadata_format(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(json.dumps(["dream-pop", "ambient"]), encoding="utf-8")

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx metadata artifact has invalid format" in status["reasons"]


def test_provider_runtime_status_reports_empty_classes_list(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(json.dumps({"classes": []}), encoding="utf-8")

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx metadata classes unavailable" in status["reasons"]


def test_provider_runtime_status_reports_invalid_class_labels(tmp_path, monkeypatch):
    model_path = tmp_path / "msd-musicnn-1.onnx"
    metadata_path = tmp_path / "msd-musicnn-1.json"
    model_path.write_bytes(b"stub model")
    metadata_path.write_text(json.dumps({"classes": ["", None]}), encoding="utf-8")

    provider = _build_provider(model_path=model_path, metadata_path=metadata_path)
    monkeypatch.setattr(provider, "_load_onnxruntime", lambda: object())
    monkeypatch.setattr(
        provider,
        "_load_essentia_standard",
        lambda: SimpleNamespace(TensorflowInputMusiCNN=object()),
    )

    status = provider.describe_runtime_status()

    assert status["available"] is False
    assert "onnx metadata classes contain invalid labels" in status["reasons"]


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
