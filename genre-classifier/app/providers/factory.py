from app.providers.stub import StubGenreProvider


def get_genre_provider(settings):
    provider_name = settings.get_configured_genre_provider_name()

    if provider_name == "stub":
        return StubGenreProvider()

    if provider_name == "legacy_musicnn":
        raise ValueError(
            "GENRE_PROVIDER=legacy_musicnn is configured, but the legacy provider adapter is not wired through the provider factory yet"
        )

    raise ValueError("Unknown GENRE_PROVIDER: {}".format(provider_name))
