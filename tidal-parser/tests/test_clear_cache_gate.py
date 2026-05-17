import pytest
from starlette.requests import Request

from app import main
from app import settings


def _valid_result():
    return {
        "source_url": "https://tidal.com/browse/track/123",
        "entity_type": "track",
        "tidal_id": "123",
        "artist": "Artist",
        "title": "Title",
        "album": "Album",
        "genres": ["rock"],
        "meta_source_url": "https://example.com/release",
        "source_name": "Discogs",
        "note": None,
        "release_year": 2024,
        "country": "United States",
        "artist_country_tag": "american",
        "release_kind": "single",
        "mb_release_date": "2024-01-01",
        "mb_confidence": 0.9,
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "final_genres": ["rock"],
        "audio_note": None,
        "from_cache": False,
        "blog_output": {"line1": "Artist - Title", "line2": "#music"},
    }


def _make_request(method="POST", path="/clear-cache"):
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }
    return Request(scope)


def test_clear_cache_enabled_defaults_to_true(monkeypatch):
    monkeypatch.delenv("CLEAR_CACHE_ENABLED", raising=False)

    assert settings.is_clear_cache_enabled() is True


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "0",
        "no",
        "off",
    ],
)
def test_clear_cache_enabled_false_values(monkeypatch, value):
    monkeypatch.setenv("CLEAR_CACHE_ENABLED", value)

    assert settings.is_clear_cache_enabled() is False


@pytest.mark.parametrize(
    "value",
    [
        "true",
        "1",
        "yes",
        "on",
    ],
)
def test_clear_cache_enabled_true_values(monkeypatch, value):
    monkeypatch.setenv("CLEAR_CACHE_ENABLED", value)

    assert settings.is_clear_cache_enabled() is True


@pytest.mark.asyncio
async def test_clear_cache_route_returns_403_and_skips_cache_helpers_when_disabled(monkeypatch):
    monkeypatch.setattr(main.settings, "is_clear_cache_enabled", lambda: False)

    def _unexpected_call(*args, **kwargs):
        raise AssertionError("cache helper should not be called when clear-cache is disabled")

    monkeypatch.setattr(main, "get_cached_result", _unexpected_call)
    monkeypatch.setattr(main, "delete_cached_result", _unexpected_call)
    monkeypatch.setattr(main, "build_result", _unexpected_call)

    response = await main.clear_cache(_make_request(), url="https://tidal.com/browse/track/123")

    assert response.status_code == 403
    assert response.context["error"] == "Сброс кэша отключён администратором."


@pytest.mark.parametrize("enabled, should_contain", [(True, True), (False, False)])
def test_result_page_clear_cache_button_respects_gate(monkeypatch, enabled, should_contain):
    monkeypatch.setattr(main.settings, "is_clear_cache_enabled", lambda: enabled)

    html = main.templates.get_template("index.html").render(
        request=_make_request("POST", "/"),
        result=_valid_result(),
        error=None,
        error_request_id=None,
        form_url="https://tidal.com/browse/track/123",
        form_manual_release_type="auto",
        clear_cache_enabled=enabled,
    )

    assert ('action="/clear-cache"' in html) is should_contain
