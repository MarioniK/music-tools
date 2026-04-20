import sys
import types
from pathlib import Path

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
