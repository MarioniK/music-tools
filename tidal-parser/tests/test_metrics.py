import json

import httpx
import pytest
from starlette.requests import Request

from app import main
from app import metrics
from app.services import discogs
from app.services import musicbrainz


@pytest.fixture(autouse=True)
def reset_metrics_state():
    metrics.reset()
    yield
    metrics.reset()


def _make_request(method="GET", path="/api/parse"):
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
    request = Request(scope)
    request.state.request_id = "req-metrics"
    return request


def _valid_result():
    return {
        "source_url": "https://tidal.com/browse/track/123",
        "entity_type": "track",
        "tidal_id": "123",
        "artist": "Artist",
        "title": "Track Title",
        "album": "Album Title",
        "genres": ["rock"],
        "meta_source_url": "https://example.com/source",
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
        "blog_output": {"line1": "Artist - Track", "line2": "#music"},
    }


def test_metrics_registry_increment_snapshot_and_reset():
    registry = metrics.MetricsRegistry(["foo_total", "bar_total"])

    registry.increment("foo_total")
    registry.increment("foo_total", value=2)
    registry.increment("bar_total")

    assert registry.snapshot() == {"foo_total": 3, "bar_total": 1}

    registry.reset()
    assert registry.snapshot() == {"foo_total": 0, "bar_total": 0}


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_snapshot():
    metrics.increment_requests_total()
    metrics.increment_cache_hit_total()

    body = await main.get_metrics()
    assert body["started_at"]
    assert body["generated_at"]
    assert isinstance(body["uptime_seconds"], int)
    assert body["counters"]["requests_total"] == 1
    assert body["counters"]["cache_hit_total"] == 1
    assert body["metrics"]["requests_total"] == 1
    assert body["metrics"]["cache_hit_total"] == 1


def test_metrics_snapshot_with_metadata_is_deterministic():
    wall_clock_values = iter([1_700_000_000.0, 1_700_000_005.0])
    monotonic_values = iter([100.0, 105.0])
    registry = metrics.MetricsRegistry(
        metrics.METRIC_NAMES,
        time_provider=lambda: next(wall_clock_values),
        monotonic_provider=lambda: next(monotonic_values),
    )

    registry.increment(metrics.REQUESTS_TOTAL)
    registry.increment(metrics.PARSE_SUCCESS_TOTAL)
    registry.increment(metrics.DEGRADED_RESULT_TOTAL)
    registry.increment(metrics.CACHE_HIT_TOTAL)
    registry.increment(metrics.CACHE_MISS_TOTAL)
    registry.increment(metrics.DISCOGS_FAILURE_TOTAL)
    registry.increment(metrics.MUSICBRAINZ_FAILURE_TOTAL)

    snapshot = registry.snapshot_with_metadata()

    assert snapshot["started_at"] == "2023-11-14T22:13:20Z"
    assert snapshot["generated_at"] == "2023-11-14T22:13:25Z"
    assert snapshot["uptime_seconds"] == 5
    assert snapshot["counters"][metrics.REQUESTS_TOTAL] == 1
    assert snapshot["metrics"][metrics.REQUESTS_TOTAL] == 1
    assert snapshot["summary"] == {
        "totals": {
            "completed_requests_total": 1,
            "source_failure_total": 2,
        },
        "ratios": {
            "cache_hit_ratio": 0.5,
            "degraded_result_ratio": 1.0,
        },
    }


def test_metrics_reset_keeps_started_at_and_uptime_baseline():
    wall_clock_values = iter([1_700_000_000.0, 1_700_000_005.0])
    monotonic_values = iter([100.0, 105.0])
    registry = metrics.MetricsRegistry(
        metrics.METRIC_NAMES,
        time_provider=lambda: next(wall_clock_values),
        monotonic_provider=lambda: next(monotonic_values),
    )

    registry.increment(metrics.REQUESTS_TOTAL)
    registry.reset()

    snapshot = registry.snapshot_with_metadata()

    assert snapshot["started_at"] == "2023-11-14T22:13:20Z"
    assert snapshot["generated_at"] == "2023-11-14T22:13:25Z"
    assert snapshot["uptime_seconds"] == 5
    assert snapshot["counters"][metrics.REQUESTS_TOTAL] == 0


@pytest.mark.asyncio
async def test_parse_api_success_updates_orchestration_metrics(monkeypatch):
    async def fake_build_result(url, force_refresh=False, baseline=None):
        return _valid_result()

    monkeypatch.setattr(main, "build_result", fake_build_result)
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)

    response = await parse_api_handler(
        _make_request(method="GET", path="/api/parse"),
        url="https://tidal.com/browse/track/123",
        force_refresh=0,
    )

    assert response["ok"] is True
    assert metrics.snapshot()["requests_total"] == 1
    assert metrics.snapshot()["parse_success_total"] == 1
    assert metrics.snapshot()["parse_error_total"] == 0


@pytest.mark.asyncio
async def test_parse_api_error_updates_orchestration_metrics():
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)

    response = await parse_api_handler(
        _make_request(method="GET", path="/api/parse"),
        url="",
        force_refresh=0,
    )

    assert response.status_code == 400
    assert json.loads(response.body)["request_id"] == "req-metrics"
    assert metrics.snapshot()["requests_total"] == 1
    assert metrics.snapshot()["parse_error_total"] == 1
    assert metrics.snapshot()["parse_success_total"] == 0


@pytest.mark.asyncio
async def test_build_result_updates_cache_hit_counter(monkeypatch):
    cached = _valid_result()
    cached["from_cache"] = True

    monkeypatch.setattr(main, "get_cached_result", lambda cache_key: dict(cached))

    result = await main.build_result("https://tidal.com/browse/track/123", force_refresh=False)

    assert result["from_cache"] is True
    assert metrics.snapshot()["cache_hit_total"] == 1
    assert metrics.snapshot()["cache_miss_total"] == 0


@pytest.mark.asyncio
async def test_build_result_updates_cache_miss_force_refresh_and_degraded_counters(monkeypatch):
    degraded = _valid_result()
    degraded["note"] = "Discogs не нашёл подходящий релиз."

    async def fake_compute_result(url):
        return dict(degraded)

    monkeypatch.setattr(main, "get_cached_result", lambda cache_key: None)
    monkeypatch.setattr(main, "compute_result", fake_compute_result)
    monkeypatch.setattr(main, "merge_prefer_better", lambda previous, result: result)
    monkeypatch.setattr(main, "save_cached_result", lambda result: None)

    result = await main.build_result("https://tidal.com/browse/track/123", force_refresh=True)

    assert result["note"] == degraded["note"]
    snapshot = metrics.snapshot()
    assert snapshot["cache_hit_total"] == 0
    assert snapshot["cache_miss_total"] == 1
    assert snapshot["force_refresh_total"] == 1
    assert snapshot["degraded_result_total"] == 1


@pytest.mark.asyncio
async def test_discogs_success_updates_metrics(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        if "database/search" in url:
            return {
                "results": [
                    {
                        "title": "Artist - Release Title",
                        "year": 2024,
                        "uri": "/release/2",
                        "resource_url": "https://api.discogs.com/releases/2",
                    }
                ]
            }

        return {
            "title": "Release Title",
            "year": 2024,
            "uri": "/release/2",
            "genres": ["Rock"],
            "styles": ["Indie Rock"],
            "artists": [{"name": "Artist"}],
        }

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["note"] is None
    assert metrics.snapshot()["discogs_success_total"] == 1
    assert metrics.snapshot()["discogs_not_found_total"] == 0
    assert metrics.snapshot()["discogs_failure_total"] == 0


@pytest.mark.asyncio
async def test_discogs_not_found_updates_metrics(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        return {"results": []}

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["note"] == "Discogs не нашёл подходящий релиз."
    assert metrics.snapshot()["discogs_not_found_total"] == 1


@pytest.mark.asyncio
async def test_discogs_failure_updates_metrics(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert "Таймаут запроса к Discogs" in result["note"]
    assert metrics.snapshot()["discogs_failure_total"] == 1


@pytest.mark.asyncio
async def test_musicbrainz_success_updates_metrics(monkeypatch):
    async def fake_fetch_with_retry(url, params, context):
        return {
            "outcome": "success",
            "data": {
                "releases": [
                    {
                        "title": "Album Title",
                        "date": "2024-01-01",
                        "artist-credit": [{"name": "Artist", "artist": {"id": "artist-1"}}],
                        "release-group": {"primary-type": "Album", "secondary-types": []},
                    }
                ]
            },
            "status_code": None,
            "error": None,
        }

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch_with_retry)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album Title", None, "album")

    assert result["outcome"] == "success"
    assert metrics.snapshot()["musicbrainz_success_total"] == 1
    assert metrics.snapshot()["musicbrainz_not_found_total"] == 0
    assert metrics.snapshot()["musicbrainz_failure_total"] == 0


@pytest.mark.asyncio
async def test_musicbrainz_not_found_updates_metrics(monkeypatch):
    async def fake_fetch_with_retry(url, params, context):
        return {
            "outcome": "success",
            "data": {"releases": []},
            "status_code": None,
            "error": None,
        }

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch_with_retry)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album Title", None, "album")

    assert result["outcome"] == "not_found"
    assert metrics.snapshot()["musicbrainz_not_found_total"] == 1


@pytest.mark.asyncio
async def test_musicbrainz_failure_updates_metrics(monkeypatch):
    async def fake_fetch_with_retry(url, params, context):
        return {
            "outcome": "timeout",
            "data": None,
            "status_code": None,
            "error": "timeout",
        }

    monkeypatch.setattr(musicbrainz, "fetch_musicbrainz_json_with_retry", fake_fetch_with_retry)

    result = await musicbrainz.search_musicbrainz_release_info("Artist", "Album Title", None, "album")

    assert result["outcome"] == "timeout"
    assert metrics.snapshot()["musicbrainz_failure_total"] == 1
