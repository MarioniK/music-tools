import httpx
import pytest

from app.services import musicbrainz


def _make_monotonic(values):
    state = {"values": list(values), "index": 0}

    def fake_monotonic():
        index = state["index"]
        values_list = state["values"]
        if index >= len(values_list):
            return values_list[-1]

        state["index"] = index + 1
        return values_list[index]

    return fake_monotonic


@pytest.fixture(autouse=True)
def reset_musicbrainz_rate_limit_state(monkeypatch):
    monkeypatch.setattr(musicbrainz, "_musicbrainz_rate_limit_lock", None)
    monkeypatch.setattr(musicbrainz, "_musicbrainz_last_request_started_at", None)


def test_build_musicbrainz_headers_uses_configured_contact_email(monkeypatch):
    monkeypatch.setenv("MUSICBRAINZ_CONTACT_EMAIL", "contact@test.invalid")
    monkeypatch.setattr(musicbrainz, "_missing_contact_email_warned", False)

    headers = musicbrainz.build_musicbrainz_headers()

    assert headers["User-Agent"] == "tidal-parser/1.0 (contact@test.invalid)"
    assert headers["Accept"] == "application/json"


def test_build_musicbrainz_headers_without_contact_email_uses_safe_fallback(monkeypatch, caplog):
    monkeypatch.delenv("MUSICBRAINZ_CONTACT_EMAIL", raising=False)
    monkeypatch.setattr(musicbrainz, "_missing_contact_email_warned", False)

    with caplog.at_level("WARNING"):
        headers = musicbrainz.build_musicbrainz_headers()

    assert headers["User-Agent"] == "tidal-parser/1.0"
    assert "missing_contact_email" in caplog.text


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_success_without_rate_limit_wait(monkeypatch):
    sleep_calls = []
    client_calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, headers):
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, follow_redirects=False):
            client_calls.append(
                {
                    "url": url,
                    "params": params,
                    "follow_redirects": follow_redirects,
                    "headers": self.headers,
                }
            )

            class Response:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"ok": True}

            return Response()

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.delenv("MUSICBRAINZ_CONTACT_EMAIL", raising=False)
    monkeypatch.setattr(musicbrainz.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(musicbrainz.time, "monotonic", _make_monotonic([10.0, 10.0]))

    result = await musicbrainz.fetch_musicbrainz_json("https://musicbrainz.test", {"q": "x"})

    assert result == {"ok": True}
    assert sleep_calls == []
    assert client_calls[0]["url"] == "https://musicbrainz.test"
    assert client_calls[0]["params"] == {"q": "x"}


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_two_sequential_calls_wait_for_rate_limit(monkeypatch, caplog):
    sleep_calls = []
    client_calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, headers):
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, follow_redirects=False):
            client_calls.append(url)

            class Response:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"ok": True}

            return Response()

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.delenv("MUSICBRAINZ_CONTACT_EMAIL", raising=False)
    monkeypatch.setattr(musicbrainz.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(musicbrainz.time, "monotonic", _make_monotonic([10.0, 10.0, 10.3, 11.4]))

    with caplog.at_level("INFO"):
        await musicbrainz.fetch_musicbrainz_json("https://musicbrainz.test/1", {})
        await musicbrainz.fetch_musicbrainz_json("https://musicbrainz.test/2", {})

    assert client_calls == ["https://musicbrainz.test/1", "https://musicbrainz.test/2"]
    assert sleep_calls == [pytest.approx(0.8, abs=1e-6)]
    assert "event=musicbrainz_rate_limit outcome=wait" in caplog.text


@pytest.mark.asyncio
async def test_fetch_musicbrainz_json_skips_sleep_when_interval_already_elapsed(monkeypatch):
    sleep_calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, headers):
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, follow_redirects=False):
            class Response:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"ok": True}

            return Response()

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.delenv("MUSICBRAINZ_CONTACT_EMAIL", raising=False)
    monkeypatch.setattr(musicbrainz.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(musicbrainz.time, "monotonic", _make_monotonic([10.0, 10.0, 11.2, 11.2]))

    await musicbrainz.fetch_musicbrainz_json("https://musicbrainz.test/1", {})
    await musicbrainz.fetch_musicbrainz_json("https://musicbrainz.test/2", {})

    assert sleep_calls == []


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
async def test_fetch_musicbrainz_json_with_retry_second_attempt_passes_through_rate_limit(monkeypatch):
    request_calls = {"count": 0}
    sleep_calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, headers):
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, follow_redirects=False):
            request_calls["count"] += 1
            if request_calls["count"] == 1:
                raise httpx.TimeoutException("timeout")

            class Response:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"ok": True}

            return Response()

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.delenv("MUSICBRAINZ_CONTACT_EMAIL", raising=False)
    monkeypatch.setattr(musicbrainz.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(musicbrainz.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(musicbrainz.time, "monotonic", _make_monotonic([10.0, 10.0, 10.1, 11.2]))

    result = await musicbrainz.fetch_musicbrainz_json_with_retry("url", {}, "test")

    assert result["outcome"] == "success"
    assert request_calls["count"] == 2
    assert sleep_calls[0] == musicbrainz.MUSICBRAINZ_RETRY_DELAY_S
    assert sleep_calls[1] == pytest.approx(1.0, abs=1e-6)


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
