import httpx
import pytest

from app.services import musicbrainz


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_timeout_then_success(monkeypatch):
    calls = {"count": 0}

    async def fake_fetch(url, params):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.TimeoutException("timeout")
        return {"ok": True}

    async def fake_sleep(delay):
        return None

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "success"
    assert result["data"] == {"ok": True}
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_timeout_exhausted(monkeypatch):
    calls = {"count": 0}

    async def fake_fetch(url, params):
        calls["count"] += 1
        raise httpx.TimeoutException("timeout")

    async def fake_sleep(delay):
        return None

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "timeout"
    assert calls["count"] == musicbrainz.MUSICBRAINZ_MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_request_failed_exhausted(monkeypatch):
    calls = {"count": 0}

    async def fake_fetch(url, params):
        calls["count"] += 1
        raise httpx.RequestError("network", request=httpx.Request("GET", url))

    async def fake_sleep(delay):
        return None

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "request_failed"
    assert calls["count"] == musicbrainz.MUSICBRAINZ_MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_http_5xx_retries(monkeypatch):
    calls = {"count": 0}

    async def fake_fetch(url, params):
        calls["count"] += 1
        if calls["count"] == 1:
            request = httpx.Request("GET", url)
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("server error", request=request, response=response)
        return {"ok": True}

    async def fake_sleep(delay):
        return None

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "success"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_http_4xx_no_retry(monkeypatch):
    calls = {"count": 0}

    async def fake_fetch(url, params):
        calls["count"] += 1
        request = httpx.Request("GET", url)
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError("not found", request=request, response=response)

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "http_error"
    assert result["status_code"] == 404
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_with_retry_unexpected_error(monkeypatch):
    async def fake_fetch(url, params):
        raise RuntimeError("boom")

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json", fake_fetch)

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "unexpected_error"


@pytest.mark.asyncio
async def test_search_musicbrainz_release_info_success(monkeypatch):
    async def fake_fetch(url, params, context):
        return {
            "outcome": "success",
            "data": {
                "releases": [
                    {
                        "title": "Album",
                        "date": "2024-01-01",
                        "artist-credit": [{"name": "Artist", "artist": {"id": "mbid-1"}}],
                        "release-group": {"primary-type": "Album", "secondary-types": []},
                    }
                ]
            },
            "status_code": None,
            "error": None,
        }

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album", None, "album")

    assert result["outcome"] == "success"
    assert result["release_year"] == 2024
    assert result["artist_id"] == "mbid-1"


@pytest.mark.asyncio
async def test_search_musicbrainz_release_info_not_found(monkeypatch):
    async def fake_fetch(url, params, context):
        return {"outcome": "success", "data": {"releases": []}, "status_code": None, "error": None}

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album", None, "album")

    assert result["outcome"] == "not_found"


@pytest.mark.asyncio
async def test_search_musicbrainz_release_info_failure_not_treated_as_not_found(monkeypatch):
    async def fake_fetch(url, params, context):
        return {"outcome": "timeout", "data": None, "status_code": None, "error": "timeout"}

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album", None, "album")

    assert result["outcome"] == "timeout"


@pytest.mark.asyncio
async def test_search_artist_country_tag_success(monkeypatch):
    async def fake_fetch(url, params, context):
        return {
            "outcome": "success",
            "data": {"artists": [{"name": "Artist", "country": "US"}]},
            "status_code": None,
            "error": None,
        }

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch)

    result = await musicbrainz.search_artist_country_tag("Artist")

    assert result == "american"


@pytest.mark.asyncio
async def test_search_artist_country_tag_not_found(monkeypatch):
    async def fake_fetch(url, params, context):
        return {"outcome": "success", "data": {"artists": []}, "status_code": None, "error": None}

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch)

    result = await musicbrainz.search_artist_country_tag("Artist")

    assert result is None


@pytest.mark.asyncio
async def test_search_artist_country_tag_mbid_failure_does_not_fallback(monkeypatch):
    async def fake_country_by_mbid_result(artist_id):
        return {"outcome": "timeout", "country_tag": None}

    monkeypatch.setattr(musicbrainz, "get_artist_country_by_mbid_result", fake_country_by_mbid_result)

    result = await musicbrainz.search_artist_country_tag("Artist", artist_id="mbid-1")

    assert result is None
