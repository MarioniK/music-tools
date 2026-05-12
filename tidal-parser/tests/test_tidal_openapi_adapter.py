import pytest

from app import tidal_openapi


def test_build_tidal_openapi_search_query_strips_terminal_punctuation():
    assert tidal_openapi.build_tidal_openapi_search_query("The Lemon Twigs", 'Look For Your Mind!') == "The Lemon Twigs Look For Your Mind"


@pytest.mark.asyncio
async def test_missing_credentials_returns_disabled_state(monkeypatch):
    monkeypatch.delenv("TIDAL_CLIENT_ID", raising=False)
    monkeypatch.delenv("TIDAL_CLIENT_SECRET", raising=False)
    tidal_openapi.reset_tidal_openapi_state()

    result = await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", "album", 2001)

    assert result["state"] == "disabled"
    assert result["candidates"] == []
    assert "ручной поиск" in result["message"].lower()


@pytest.mark.asyncio
async def test_token_request_and_albums_relationship_parses_candidates(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    calls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "data": data,
                "params": params or {},
            }
        )
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        assert "/relationships/albums" in url
        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {
                "data": [{"id": "1108027", "type": "albums"}],
                "included": [
                    {
                        "id": "1108027",
                        "type": "albums",
                        "attributes": {
                            "title": "Chaos A.D.",
                            "releaseDate": "1993-01-01",
                        },
                    }
                ],
            },
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    result = await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", "album", 2001)

    assert result["state"] == "success"
    assert result["query"] == "Sepultura Nation"
    assert result["candidates"][0]["id"] == "1108027"
    assert result["candidates"][0]["type"] == "album"
    assert result["candidates"][0]["title"] == "Chaos A.D."
    assert result["candidates"][0]["release_date"] == "1993-01-01"
    assert result["candidates"][0]["year"] == "1993"
    assert result["candidates"][0]["tidal_url"] == "https://tidal.com/album/1108027"
    assert any(call["url"] == tidal_openapi.TIDAL_TOKEN_URL for call in calls)
    assert any("/relationships/albums" in call["url"] for call in calls)


@pytest.mark.asyncio
async def test_query_excludes_year(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    captured_urls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        captured_urls.append(url)
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {"data": [], "included": []},
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", "album", 2001)

    relationship_url = next(url for url in captured_urls if "/relationships/albums" in url)
    assert "2001" not in relationship_url
    assert "Sepultura+Nation" in relationship_url


@pytest.mark.asyncio
async def test_title_punctuation_is_removed_before_request_dispatch(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    captured_urls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        captured_urls.append(url)
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {
                "data": [{"id": "498548519", "type": "albums"}],
                "included": [
                    {
                        "id": "498548519",
                        "type": "albums",
                        "attributes": {
                            "title": "Look For Your Mind!",
                            "releaseDate": "2026-05-08",
                        },
                    }
                ],
            },
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    result = await tidal_openapi.lookup_tidal_candidates("The Lemon Twigs", "Look For Your Mind!", "album", 2026)

    assert result["state"] == "success"
    assert result["query"] == "The Lemon Twigs Look For Your Mind"
    relationship_url = next(url for url in captured_urls if "/relationships/albums" in url)
    assert "The+Lemon+Twigs+Look+For+Your+Mind" in relationship_url
    assert "%20" not in relationship_url
    assert result["candidates"][0]["id"] == "498548519"
    assert result["candidates"][0]["title"] == "Look For Your Mind!"
    assert result["candidates"][0]["release_date"] == "2026-05-08"
    assert result["candidates"][0]["tidal_url"] == "https://tidal.com/album/498548519"


@pytest.mark.asyncio
async def test_album_release_type_uses_albums_relationship_endpoint(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    captured_urls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        captured_urls.append(url)
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {"data": [], "included": []},
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    result = await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", "album", 2001)

    assert result["state"] == "empty"
    assert any("/relationships/albums" in url for url in captured_urls)
    assert not any("/relationships/tracks" in url for url in captured_urls)


@pytest.mark.asyncio
async def test_track_release_type_uses_tracks_relationship_endpoint(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    captured_urls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        captured_urls.append(url)
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {"data": [], "included": []},
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    result = await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", "single", 2001)

    assert result["state"] == "empty"
    assert any("/relationships/tracks" in url for url in captured_urls)
    assert not any("/relationships/albums" in url for url in captured_urls if url != tidal_openapi.TIDAL_TOKEN_URL)


@pytest.mark.asyncio
async def test_unknown_release_type_uses_limited_albums_then_tracks_lookup(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "client-secret")
    tidal_openapi.reset_tidal_openapi_state()

    captured_urls = []

    async def fake_request_json(method, url, headers=None, data=None, params=None):
        captured_urls.append(url)
        if url == tidal_openapi.TIDAL_TOKEN_URL:
            return {
                "status": 200,
                "content_type": "application/json",
                "json": {
                    "access_token": "access-token",
                    "token_type": "Bearer",
                    "expires_in": 14400,
                },
            }

        if "/relationships/albums" in url:
            return {
                "status": 200,
                "content_type": "application/vnd.api+json",
                "json": {"data": [], "included": []},
            }

        assert "/relationships/tracks" in url
        return {
            "status": 200,
            "content_type": "application/vnd.api+json",
            "json": {
                "data": [{"id": "705195", "type": "tracks"}],
                "included": [
                    {
                        "id": "705195",
                        "type": "tracks",
                        "attributes": {
                            "title": "Sangue latino",
                            "releaseDate": "1985-01-01",
                        },
                    }
                ],
            },
        }

    monkeypatch.setattr(tidal_openapi, "_request_json", fake_request_json)

    result = await tidal_openapi.lookup_tidal_candidates("Sepultura", "Nation", None, 2001)

    assert result["state"] == "success"
    assert result["candidates"][0]["id"] == "705195"
    assert any("/relationships/albums" in url for url in captured_urls)
    assert any("/relationships/tracks" in url for url in captured_urls)
    assert len([url for url in captured_urls if "/relationships/" in url]) == 2


@pytest.mark.asyncio
async def test_candidate_url_construction():
    assert tidal_openapi.build_tidal_candidate_url("albums", "1108027") == "https://tidal.com/album/1108027"
    assert tidal_openapi.build_tidal_candidate_url("tracks", "705195") == "https://tidal.com/track/705195"
