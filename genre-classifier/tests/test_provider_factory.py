from types import SimpleNamespace

import pytest

from app.providers.base import ProviderResult
from app.providers.factory import get_genre_provider
from app.providers.stub import StubGenreProvider


def test_factory_selects_stub_provider():
    settings = SimpleNamespace(get_configured_genre_provider_name=lambda: "stub")

    provider = get_genre_provider(settings)

    assert isinstance(provider, StubGenreProvider)


def test_factory_rejects_unknown_provider():
    settings = SimpleNamespace(get_configured_genre_provider_name=lambda: "unknown")

    with pytest.raises(ValueError, match="Unknown GENRE_PROVIDER: unknown"):
        get_genre_provider(settings)


def test_factory_rejects_legacy_placeholder_provider():
    settings = SimpleNamespace(get_configured_genre_provider_name=lambda: "legacy_musicnn")

    with pytest.raises(
        ValueError,
        match="GENRE_PROVIDER=legacy_musicnn is configured, but the legacy provider adapter is not wired through the provider factory yet",
    ):
        get_genre_provider(settings)


def test_stub_provider_returns_expected_result_shape():
    provider = StubGenreProvider()

    result = provider.classify("/tmp/audio.wav")

    assert isinstance(result, ProviderResult)
    assert result.provider_name == "stub"
    assert result.model_name == "stub-v1"
    assert len(result.genres) == 1
    assert result.genres[0].tag == "stub genre"
    assert result.genres[0].score == 1.0
