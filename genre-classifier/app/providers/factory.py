from app.providers.legacy_musicnn import LegacyMusiCNNProvider
from app.providers.stub import StubGenreProvider


def get_genre_provider(settings):
    provider_name = settings.get_configured_genre_provider_name()

    if provider_name == "stub":
        return StubGenreProvider()

    if provider_name == "legacy_musicnn":
        return LegacyMusiCNNProvider()

    raise ValueError("Unknown GENRE_PROVIDER: {}".format(provider_name))
