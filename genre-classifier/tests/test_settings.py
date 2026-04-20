from app.core import settings


def test_get_configured_genre_provider_name_defaults_to_legacy(monkeypatch):
    monkeypatch.delenv("GENRE_PROVIDER", raising=False)

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_LEGACY


def test_get_configured_genre_provider_name_accepts_explicit_llm(monkeypatch):
    monkeypatch.setenv("GENRE_PROVIDER", settings.GENRE_PROVIDER_LLM)

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_LLM


def test_get_configured_genre_provider_name_falls_back_to_default_for_blank_value(monkeypatch):
    monkeypatch.setenv("GENRE_PROVIDER", "   ")

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_LEGACY


def test_get_configured_llm_client_name_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("LLM_CLIENT", raising=False)

    assert settings.get_configured_llm_client_name() == settings.LLM_CLIENT_STUB


def test_get_configured_llm_client_name_accepts_explicit_local_http(monkeypatch):
    monkeypatch.setenv("LLM_CLIENT", settings.LLM_CLIENT_LOCAL_HTTP)

    assert settings.get_configured_llm_client_name() == settings.LLM_CLIENT_LOCAL_HTTP


def test_get_configured_llm_local_http_timeout_seconds_defaults(monkeypatch):
    monkeypatch.delenv("LLM_LOCAL_HTTP_TIMEOUT_SECONDS", raising=False)

    assert settings.get_configured_llm_local_http_timeout_seconds() == settings.DEFAULT_LLM_LOCAL_HTTP_TIMEOUT_SECONDS
