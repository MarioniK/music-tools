import sys
import types
import time
import logging
from pathlib import Path

import pytest

if "numpy" not in sys.modules:
    numpy_stub = types.ModuleType("numpy")
    numpy_stub.mean = lambda *args, **kwargs: None
    sys.modules["numpy"] = numpy_stub

if "essentia" not in sys.modules:
    essentia_stub = types.ModuleType("essentia")
    essentia_standard_stub = types.ModuleType("essentia.standard")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return []

    essentia_standard_stub.MonoLoader = _Dummy
    essentia_standard_stub.TensorflowPredictMusiCNN = _Dummy
    essentia_stub.standard = essentia_standard_stub
    sys.modules["essentia"] = essentia_stub
    sys.modules["essentia.standard"] = essentia_standard_stub

from app.providers.base import ProviderGenreScore, ProviderResult
from app.services import classify


@pytest.fixture(autouse=True)
def reset_shadow_runtime_env(monkeypatch):
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", raising=False)


def _install_successful_audio_pipeline(monkeypatch, tmp_path, *, events=None):
    class _ProductionProvider:
        def classify(self, audio_path: str) -> ProviderResult:
            if events is not None:
                events.append("production_classified")
            return ProviderResult(
                genres=[
                    ProviderGenreScore(tag="indie rock", score=0.81234),
                    ProviderGenreScore(tag="dream pop", score=0.50123),
                ],
                provider_name="legacy_musicnn",
                model_name="legacy-model",
            )

    monkeypatch.setattr(classify.settings, "TMP_DIR", tmp_path)
    monkeypatch.setattr(classify, "validate_upload", lambda file_bytes, filename: None)
    monkeypatch.setattr(classify, "normalize_audio_file", lambda input_path, output_path: Path(output_path).touch())
    monkeypatch.setattr(classify, "get_genre_provider", lambda settings_module: _ProductionProvider())


def _post_classify():
    genres, normalized = classify.process_uploaded_audio(b"audio-bytes", "track.mp3")
    return 200, {
        "ok": True,
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized,
    }


def _assert_classify_success_payload_shape(payload):
    assert set(payload.keys()) == {"ok", "message", "genres", "genres_pretty"}
    assert payload["ok"] is True
    assert payload["message"] == "Аудио проанализировано"
    assert payload["genres"] == [
        {"tag": "indie rock", "prob": 0.8123},
        {"tag": "dream pop", "prob": 0.5012},
    ]
    assert payload["genres_pretty"] == ["indie rock", "dream pop"]
    for forbidden_key in ("shadow", "llm", "comparison", "diagnostics", "canary"):
        assert forbidden_key not in payload


def test_classify_response_shape_unchanged_when_shadow_disabled(monkeypatch, tmp_path):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)

    status_code, payload = _post_classify()

    assert status_code == 200
    _assert_classify_success_payload_shape(payload)


def test_classify_response_shape_unchanged_when_shadow_enabled(monkeypatch, tmp_path, caplog):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "1.0")

    def shadow_classification(wav_path):
        return ["electronic"]

    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    with caplog.at_level(logging.INFO, logger="genre_classifier"):
        status_code, payload = _post_classify()

    assert status_code == 200
    _assert_classify_success_payload_shape(payload)
    assert any(hasattr(record, "shadow_payload") for record in caplog.records)


def test_classify_shadow_observer_not_called_when_shadow_disabled(monkeypatch, tmp_path):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)
    shadow_calls = []

    def shadow_classification(wav_path):
        shadow_calls.append(wav_path)
        return ["electronic"]

    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    status_code, payload = _post_classify()

    assert status_code == 200
    assert shadow_calls == []
    _assert_classify_success_payload_shape(payload)


def test_classify_shadow_observer_runs_after_production_response_is_built(
    monkeypatch,
    tmp_path,
):
    events = []
    _install_successful_audio_pipeline(monkeypatch, tmp_path, events=events)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "1.0")

    original_map_genres = classify.map_validated_result_to_legacy_genres
    original_map_pretty = classify.map_validated_result_to_legacy_genres_pretty

    def map_genres(validated_result):
        mapped = original_map_genres(validated_result)
        events.append("genres_built")
        return mapped

    def map_pretty(validated_result):
        mapped = original_map_pretty(validated_result)
        events.append("pretty_built")
        return mapped

    def shadow_classification(wav_path):
        events.append("shadow_called")
        return ["electronic"]

    monkeypatch.setattr(classify, "map_validated_result_to_legacy_genres", map_genres)
    monkeypatch.setattr(classify, "map_validated_result_to_legacy_genres_pretty", map_pretty)
    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    status_code, payload = _post_classify()

    assert status_code == 200
    assert events == [
        "production_classified",
        "genres_built",
        "pretty_built",
        "shadow_called",
    ]
    _assert_classify_success_payload_shape(payload)


def test_classify_shadow_exception_does_not_change_status_or_payload(
    monkeypatch,
    tmp_path,
):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "1.0")

    def shadow_classification(wav_path):
        raise RuntimeError("shadow failed")

    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    status_code, payload = _post_classify()

    assert status_code == 200
    _assert_classify_success_payload_shape(payload)


def test_classify_shadow_timeout_does_not_change_status_or_payload(
    monkeypatch,
    tmp_path,
):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "1.0")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", "0.001")

    def shadow_classification(wav_path):
        time.sleep(0.05)
        return ["electronic"]

    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    status_code, payload = _post_classify()

    assert status_code == 200
    _assert_classify_success_payload_shape(payload)


def test_classify_response_does_not_expose_shadow_diagnostics_when_enabled(
    monkeypatch,
    tmp_path,
):
    _install_successful_audio_pipeline(monkeypatch, tmp_path)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "1.0")

    def shadow_classification(wav_path):
        return ["electronic"]

    monkeypatch.setattr(classify, "_run_shadow_provider_classification", shadow_classification)

    status_code, payload = _post_classify()

    assert status_code == 200
    for forbidden_key in ("shadow", "llm", "comparison", "diagnostics", "canary"):
        assert forbidden_key not in payload


def test_process_uploaded_audio_uses_provider_factory_and_preserves_result_shape(
    monkeypatch,
    tmp_path,
):
    provider_calls = []

    class _FakeProvider:
        def classify(self, audio_path: str) -> ProviderResult:
            provider_calls.append(audio_path)
            return ProviderResult(
                genres=[
                    ProviderGenreScore(tag="indie rock", score=0.81234),
                    ProviderGenreScore(tag="dream pop", score=0.50123),
                ],
                provider_name="fake-provider",
                model_name="fake-model",
            )

    monkeypatch.setattr(classify.settings, "TMP_DIR", tmp_path)
    monkeypatch.setattr(classify, "validate_upload", lambda file_bytes, filename: None)
    monkeypatch.setattr(classify, "normalize_audio_file", lambda input_path, output_path: Path(output_path).touch())
    monkeypatch.setattr(classify, "get_genre_provider", lambda settings_module: _FakeProvider())

    genres, normalized = classify.process_uploaded_audio(b"audio-bytes", "track.mp3")

    assert len(provider_calls) == 1
    assert provider_calls[0].endswith(".wav")
    assert genres == [
        {"tag": "indie rock", "prob": 0.8123},
        {"tag": "dream pop", "prob": 0.5012},
    ]
    assert normalized == ["indie rock", "dream pop"]


def test_process_uploaded_audio_survives_partially_invalid_provider_result(
    monkeypatch,
    tmp_path,
):
    class _FakeProvider:
        def classify(self, audio_path: str) -> ProviderResult:
            return ProviderResult(
                genres=[
                    ProviderGenreScore(tag=" Indie-Rock ", score=0.81234),
                    ProviderGenreScore(tag="   ", score=0.7),
                    ProviderGenreScore(tag="dream pop", score="oops"),
                    "not-a-provider-item",
                    ProviderGenreScore(tag="dream-pop", score=0.50123),
                ],
                provider_name="fake-provider",
                model_name="fake-model",
            )

    monkeypatch.setattr(classify.settings, "TMP_DIR", tmp_path)
    monkeypatch.setattr(classify, "validate_upload", lambda file_bytes, filename: None)
    monkeypatch.setattr(classify, "normalize_audio_file", lambda input_path, output_path: Path(output_path).touch())
    monkeypatch.setattr(classify, "get_genre_provider", lambda settings_module: _FakeProvider())

    genres, normalized = classify.process_uploaded_audio(b"audio-bytes", "track.mp3")

    assert genres == [
        {"tag": "indie rock", "prob": 0.8123},
        {"tag": "dream pop", "prob": 0.5012},
    ]
    assert normalized == ["indie rock", "dream pop"]


def test_process_uploaded_audio_raises_for_fully_invalid_provider_result(
    monkeypatch,
    tmp_path,
):
    class _FakeProvider:
        def classify(self, audio_path: str) -> ProviderResult:
            return ProviderResult(
                genres=[
                    ProviderGenreScore(tag="   ", score=0.9),
                    ProviderGenreScore(tag="indie rock", score=float("nan")),
                    "not-a-provider-item",
                ],
                provider_name="fake-provider",
                model_name="fake-model",
            )

    monkeypatch.setattr(classify.settings, "TMP_DIR", tmp_path)
    monkeypatch.setattr(classify, "validate_upload", lambda file_bytes, filename: None)
    monkeypatch.setattr(classify, "normalize_audio_file", lambda input_path, output_path: Path(output_path).touch())
    monkeypatch.setattr(classify, "get_genre_provider", lambda settings_module: _FakeProvider())

    try:
        classify.process_uploaded_audio(b"audio-bytes", "track.mp3")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "no valid provider genres"
