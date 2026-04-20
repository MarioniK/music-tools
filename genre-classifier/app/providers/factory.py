from app.providers.llm import LlmGenreProvider
from app.providers.legacy_musicnn import LegacyMusiCNNProvider
from app.providers.stub import StubGenreProvider


def get_genre_provider(settings):
    provider_name = settings.get_configured_genre_provider_name()

    if provider_name == "stub":
        return StubGenreProvider()

    if provider_name == settings.GENRE_PROVIDER_LEGACY:
        return LegacyMusiCNNProvider()

    if provider_name == settings.GENRE_PROVIDER_LLM:
        return LlmGenreProvider()

    raise ValueError("Unknown GENRE_PROVIDER: {}".format(provider_name))
