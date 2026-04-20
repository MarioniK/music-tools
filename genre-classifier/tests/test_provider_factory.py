from types import SimpleNamespace

import pytest

from app.providers.base import ProviderResult
from app.providers.factory import get_genre_provider
from app.providers.llm import LlmGenreProvider
from app.providers.legacy_musicnn import LegacyMusiCNNProvider
from app.providers.stub import StubGenreProvider


def test_factory_selects_stub_provider():
    settings = SimpleNamespace(get_configured_genre_provider_name=lambda: "stub")

    provider = get_genre_provider(settings)

    assert isinstance(provider, StubGenreProvider)


def test_factory_rejects_unknown_provider():
    settings = SimpleNamespace(
        GENRE_PROVIDER_LEGACY="legacy_musicnn",
        GENRE_PROVIDER_LLM="llm",
        get_configured_genre_provider_name=lambda: "unknown",
    )

    with pytest.raises(ValueError, match="Unknown GENRE_PROVIDER: unknown"):
        get_genre_provider(settings)


def test_factory_selects_legacy_musicnn_provider():
    settings = SimpleNamespace(
        GENRE_PROVIDER_LEGACY="legacy_musicnn",
        GENRE_PROVIDER_LLM="llm",
        get_configured_genre_provider_name=lambda: "legacy_musicnn",
    )

    provider = get_genre_provider(settings)

    assert isinstance(provider, LegacyMusiCNNProvider)


def test_factory_selects_llm_provider():
    settings = SimpleNamespace(
        GENRE_PROVIDER_LEGACY="legacy_musicnn",
        GENRE_PROVIDER_LLM="llm",
        get_configured_genre_provider_name=lambda: "llm",
    )

    provider = get_genre_provider(settings)

    assert isinstance(provider, LlmGenreProvider)


def test_stub_provider_returns_expected_result_shape():
    provider = StubGenreProvider()

    result = provider.classify("/tmp/audio.wav")

    assert isinstance(result, ProviderResult)
    assert result.provider_name == "stub"
    assert result.model_name == "stub-v1"
    assert len(result.genres) == 1
    assert result.genres[0].tag == "stub genre"
    assert result.genres[0].score == 1.0


def test_legacy_musicnn_provider_maps_legacy_result_shape(monkeypatch):
    monkeypatch.setattr(
        "app.providers.legacy_musicnn._run_legacy_musicnn_classification",
        lambda audio_path: [
            {"tag": "indie rock", "prob": 0.8123},
            {"tag": "dream pop", "prob": 0.501},
        ],
    )

    provider = LegacyMusiCNNProvider()
    result = provider.classify("/tmp/audio.wav")

    assert isinstance(result, ProviderResult)
    assert result.provider_name == "legacy_musicnn"
    assert result.model_name == "msd-musicnn-1"
    assert [item.tag for item in result.genres] == ["indie rock", "dream pop"]
    assert [item.score for item in result.genres] == [0.8123, 0.501]
