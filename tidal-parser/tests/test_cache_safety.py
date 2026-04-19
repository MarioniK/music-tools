import json
import sqlite3

import pytest
from starlette.requests import Request

from app import main


def _make_test_db(tmp_path):
    db_path = tmp_path / "cache.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE parsed_cache (
            cache_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    return db_path


def _db_connection_factory(db_path):
    def _get_db_connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    return _get_db_connection


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


def _make_request(method="POST", path="/"):
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


def test_get_cached_result_returns_none_for_invalid_json(tmp_path, monkeypatch):
    db_path = _make_test_db(tmp_path)
    monkeypatch.setattr(main, "get_db_connection", _db_connection_factory(db_path))

    conn = main.get_db_connection()
    conn.execute(
        "INSERT INTO parsed_cache (cache_key, payload_json, created_at) VALUES (?, ?, ?)",
        ("key", "{bad json", 1),
    )
    conn.commit()
    conn.close()

    assert main.get_cached_result("key") is None


def test_get_cached_result_returns_none_for_invalid_payload(tmp_path, monkeypatch):
    db_path = _make_test_db(tmp_path)
    monkeypatch.setattr(main, "get_db_connection", _db_connection_factory(db_path))

    conn = main.get_db_connection()
    conn.execute(
        "INSERT INTO parsed_cache (cache_key, payload_json, created_at) VALUES (?, ?, ?)",
        ("key", json.dumps({"source_url": "https://tidal.com/track/1", "entity_type": "track"}), 1),
    )
    conn.commit()
    conn.close()

    assert main.get_cached_result("key") is None


def test_get_cached_result_normalizes_legacy_country_fields(tmp_path, monkeypatch):
    db_path = _make_test_db(tmp_path)
    monkeypatch.setattr(main, "get_db_connection", _db_connection_factory(db_path))

    legacy_payload = _valid_result()
    legacy_payload.pop("country")

    conn = main.get_db_connection()
    conn.execute(
        "INSERT INTO parsed_cache (cache_key, payload_json, created_at) VALUES (?, ?, ?)",
        ("key", json.dumps(legacy_payload), 1),
    )
    conn.commit()
    conn.close()

    cached = main.get_cached_result("key")

    assert cached["country"] == "United States"
    assert cached["artist_country_tag"] == "american"
    assert "country_tag" not in cached


def test_get_cached_result_rebuilds_blog_output_from_final_cached_fields(tmp_path, monkeypatch):
    db_path = _make_test_db(tmp_path)
    monkeypatch.setattr(main, "get_db_connection", _db_connection_factory(db_path))

    stale_payload = _valid_result()
    stale_payload["release_year"] = 2002
    stale_payload["country"] = "United States"
    stale_payload["artist_country_tag"] = "american"
    stale_payload["blog_output"] = {
        "line1": "Artist - Title (2016)",
        "line2": "#music #music2016 #artist #djdrugfm",
    }

    conn = main.get_db_connection()
    conn.execute(
        "INSERT INTO parsed_cache (cache_key, payload_json, created_at) VALUES (?, ?, ?)",
        ("key", json.dumps(stale_payload), 1),
    )
    conn.commit()
    conn.close()

    cached = main.get_cached_result("key")

    assert "#american" in cached["blog_output"]["line2"]
    assert "#music2002" in cached["blog_output"]["line2"]
    assert "#music2016" not in cached["blog_output"]["line2"]


def test_save_cached_result_does_not_persist_transient_fields(tmp_path, monkeypatch):
    db_path = _make_test_db(tmp_path)
    monkeypatch.setattr(main, "get_db_connection", _db_connection_factory(db_path))

    result = _valid_result()
    result["from_cache"] = True
    result["audio_note"] = "temporary"

    main.save_cached_result(result)

    conn = main.get_db_connection()
    row = conn.execute("SELECT payload_json FROM parsed_cache").fetchone()
    conn.close()

    payload = json.loads(row["payload_json"])
    assert "from_cache" not in payload
    assert "audio_note" not in payload
    assert payload["country"] == "United States"
    assert payload["artist_country_tag"] == "american"
    assert "country_tag" not in payload
    assert "#american" in payload["blog_output"]["line2"]
    assert "#music2024" in payload["blog_output"]["line2"]


@pytest.mark.asyncio
async def test_build_result_ignores_invalid_baseline(monkeypatch):
    computed = _valid_result()
    computed["blog_output"] = {
        "line1": "stale line",
        "line2": "#music #music2016 #djdrugfm",
    }
    saved = []

    async def fake_compute_result(url):
        return dict(computed)

    monkeypatch.setattr(main, "compute_result", fake_compute_result)
    monkeypatch.setattr(main, "get_cached_result", lambda cache_key: None)
    monkeypatch.setattr(main, "save_cached_result", lambda result: saved.append(dict(result)))

    result = await main.build_result(
        computed["source_url"],
        force_refresh=True,
        baseline={"broken": True},
    )

    assert result["source_url"] == computed["source_url"]
    assert result["entity_type"] == computed["entity_type"]
    assert result["tidal_id"] == computed["tidal_id"]
    assert result["artist"] == computed["artist"]
    assert result["title"] == computed["title"]
    assert result["album"] == computed["album"]
    assert result["genres"] == computed["genres"]
    assert result["release_year"] == computed["release_year"]
    assert result["country"] == computed["country"]
    assert result["artist_country_tag"] == computed["artist_country_tag"]
    assert result["release_kind"] == computed["release_kind"]
    assert result["mb_release_date"] == computed["mb_release_date"]
    assert result["mb_confidence"] == computed["mb_confidence"]
    assert result["final_genres"] == computed["final_genres"]
    assert "#american" in result["blog_output"]["line2"]
    assert "#music2024" in result["blog_output"]["line2"]
    assert "#music2016" not in result["blog_output"]["line2"]

    assert len(saved) == 1
    assert saved[0]["release_year"] == result["release_year"]
    assert saved[0]["country"] == result["country"]
    assert saved[0]["artist_country_tag"] == result["artist_country_tag"]
    assert saved[0]["blog_output"] == result["blog_output"]


@pytest.mark.asyncio
async def test_build_result_rebuilds_blog_output_after_merge(monkeypatch):
    computed = _valid_result()
    computed["release_year"] = None
    computed["country"] = None
    computed["artist_country_tag"] = None
    computed["blog_output"] = {
        "line1": "Artist - Title",
        "line2": "#music #music2016 #artist #djdrugfm",
    }

    baseline = _valid_result()
    baseline["release_year"] = 2002
    baseline["country"] = "United States"
    baseline["artist_country_tag"] = "american"

    saved = []

    async def fake_compute_result(url):
        return dict(computed)

    monkeypatch.setattr(main, "compute_result", fake_compute_result)
    monkeypatch.setattr(main, "get_cached_result", lambda cache_key: None)
    monkeypatch.setattr(main, "save_cached_result", lambda result: saved.append(dict(result)))

    result = await main.build_result(
        computed["source_url"],
        force_refresh=True,
        baseline=baseline,
    )

    assert result["release_year"] == 2002
    assert result["country"] == "United States"
    assert result["artist_country_tag"] == "american"
    assert "#american" in result["blog_output"]["line2"]
    assert "#music2002" in result["blog_output"]["line2"]
    assert "#music2016" not in result["blog_output"]["line2"]


@pytest.mark.asyncio
async def test_parse_form_does_not_save_audio_result_to_cache(monkeypatch):
    base_result = _valid_result()
    save_calls = []

    class DummyUpload:
        filename = "sample.mp3"

        async def read(self):
            return b"audio-bytes"

    async def fake_build_result(url, force_refresh=False, baseline=None):
        result = dict(base_result)
        result["from_cache"] = False
        return result

    monkeypatch.setattr(main, "build_result", fake_build_result)
    monkeypatch.setattr(
        main,
        "classify_audio_file",
        lambda file_bytes, filename: {
            "raw": [{"tag": "electronic", "prob": 0.9}],
            "pretty": ["electronic"],
        },
    )
    monkeypatch.setattr(main, "save_cached_result", lambda result: save_calls.append(dict(result)))

    upload = DummyUpload()
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    response = await parse_form_handler(
        _make_request(),
        url=base_result["source_url"],
        force_refresh="0",
        audio=upload,
    )

    assert response.status_code == 200
    assert save_calls == []


@pytest.mark.asyncio
async def test_parse_api_empty_input_returns_400():
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)
    request = _make_request(method="GET", path="/api/parse")
    request.state.request_id = "req-api-empty"

    response = await parse_api_handler(request, url="", force_refresh=0)

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "ok": False,
        "error": "Нужна ссылка TIDAL на track или album.",
        "request_id": "req-api-empty",
    }


@pytest.mark.asyncio
async def test_parse_api_invalid_url_returns_400():
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)
    request = _make_request(method="GET", path="/api/parse")
    request.state.request_id = "req-api-invalid"

    response = await parse_api_handler(
        request,
        url="https://example.com/not-tidal",
        force_refresh=0,
    )

    assert response.status_code == 400
    assert json.loads(response.body)["ok"] is False
    assert "Не удалось распознать ссылку TIDAL" in json.loads(response.body)["error"]
    assert json.loads(response.body)["request_id"] == "req-api-invalid"


@pytest.mark.asyncio
async def test_parse_api_internal_failure_returns_500(monkeypatch):
    async def fake_build_result(url, force_refresh=False, baseline=None):
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "build_result", fake_build_result)
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)
    request = _make_request(method="GET", path="/api/parse")
    request.state.request_id = "req-api-500"

    response = await parse_api_handler(
        request,
        url="https://tidal.com/browse/track/123",
        force_refresh=0,
    )

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "ok": False,
        "error": "Внутренняя ошибка сервера. Попробуй позже.",
        "request_id": "req-api-500",
    }


@pytest.mark.asyncio
async def test_parse_api_unexpected_exception_returns_500(monkeypatch):
    async def fake_build_result(url, force_refresh=False, baseline=None):
        raise TypeError("unexpected")

    monkeypatch.setattr(main, "build_result", fake_build_result)
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)
    request = _make_request(method="GET", path="/api/parse")
    request.state.request_id = "req-api-unexpected"

    response = await parse_api_handler(
        request,
        url="https://tidal.com/browse/track/123",
        force_refresh=0,
    )

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "ok": False,
        "error": "Внутренняя ошибка сервера. Попробуй позже.",
        "request_id": "req-api-unexpected",
    }


@pytest.mark.asyncio
async def test_parse_form_empty_input_returns_html_400():
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-form-empty"

    response = await parse_form_handler(
        request,
        url="",
        force_refresh="0",
        audio=None,
    )

    assert response.status_code == 400
    body = response.body.decode("utf-8")
    assert "Нужна ссылка TIDAL на track или album." in body
    assert "Reference ID: req-form-empty" in body


@pytest.mark.asyncio
async def test_parse_form_invalid_url_returns_html_400():
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-form-invalid"

    response = await parse_form_handler(
        request,
        url="https://example.com/not-tidal",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 400
    assert "Не удалось распознать ссылку TIDAL" in body
    assert "Reference ID: req-form-invalid" in body


@pytest.mark.asyncio
async def test_parse_form_internal_failure_returns_html_500(monkeypatch):
    async def fake_build_result(url, force_refresh=False, baseline=None):
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "build_result", fake_build_result)
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-form-500"

    response = await parse_form_handler(
        request,
        url="https://tidal.com/browse/track/123",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 500
    assert "Не удалось обработать запрос. Попробуй ещё раз позже." in body
    assert "Reference ID: req-form-500" in body
    assert "db down" not in body


@pytest.mark.asyncio
async def test_parse_api_recoverable_degraded_result_stays_200(monkeypatch):
    degraded = _valid_result()
    degraded["note"] = "Discogs не нашёл подходящий релиз."

    async def fake_build_result(url, force_refresh=False, baseline=None):
        return dict(degraded)

    monkeypatch.setattr(main, "build_result", fake_build_result)
    parse_api_handler = getattr(main.parse_api, "__wrapped__", main.parse_api)

    response = await parse_api_handler(
        _make_request(method="GET", path="/api/parse"),
        url="https://tidal.com/browse/track/123",
        force_refresh=0,
    )

    assert response["ok"] is True
    assert response["data"]["note"] == degraded["note"]


@pytest.mark.asyncio
async def test_compute_result_ignores_musicbrainz_failure_but_still_looks_up_country_by_artist(monkeypatch):
    country_calls = []

    async def fake_run_timed_stage(stage, coro):
        return await coro

    async def fake_parse_tidal(url):
        return {
            "source_url": url,
            "entity_type": "track",
            "tidal_id": "123",
            "artist": "Artist",
            "title": "Track Title",
            "album": "Album Title",
        }

    async def fake_search_discogs_release_metadata(artist, release_title):
        return {
            "genres": ["rock"],
            "meta_source_url": "https://example.com/discogs",
            "source_name": "Discogs",
            "note": None,
            "release_year": 2024,
        }

    async def fake_search_musicbrainz_release_info(artist, title, album, entity_type):
        return {
            "release_year": 1999,
            "release_date": "1999-01-01",
            "release_kind": "ep",
            "artist_id": "mbid-1",
            "confidence": 0.99,
            "outcome": "timeout",
        }

    async def fake_search_artist_country_tag(artist, artist_id=None):
        country_calls.append((artist, artist_id))
        return "american"

    monkeypatch.setattr(main, "run_timed_stage", fake_run_timed_stage)
    monkeypatch.setattr(main, "parse_tidal", fake_parse_tidal)
    monkeypatch.setattr(main, "search_discogs_release_metadata", fake_search_discogs_release_metadata)
    monkeypatch.setattr(main, "search_musicbrainz_release_info", fake_search_musicbrainz_release_info)
    monkeypatch.setattr(main, "search_artist_country_tag", fake_search_artist_country_tag)

    result = await main.compute_result("https://tidal.com/browse/track/123")

    assert result["release_year"] == 2024
    assert result["release_kind"] == "single"
    assert result["country"] == "United States"
    assert result["artist_country_tag"] == "american"
    assert result["genres"] == ["rock"]
    assert result["source_name"] == "Discogs"
    assert "outcome" not in result
    assert country_calls == [("Artist", None)]


def test_build_blog_output_uses_country_tag_not_display_country():
    result = _valid_result()

    blog_output = main.build_blog_output(result)

    assert "#american" in blog_output["line2"]
    assert "#unitedstates" not in blog_output["line2"]


def test_merge_prefer_better_does_not_preserve_stale_note():
    old_result = _valid_result()
    old_result["note"] = "stale note"
    old_result["release_year"] = None
    old_result["country"] = None
    old_result["artist_country_tag"] = None
    old_result["release_kind"] = None
    old_result["mb_release_date"] = None
    old_result["mb_confidence"] = None
    old_result["genres"] = []
    old_result["source_name"] = None
    old_result["meta_source_url"] = None

    new_result = _valid_result()
    new_result["note"] = None

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["note"] is None


def test_merge_prefer_better_keeps_stronger_metadata():
    old_result = _valid_result()
    new_result = _valid_result()
    new_result["release_year"] = None
    new_result["country"] = None
    new_result["artist_country_tag"] = None
    new_result["mb_release_date"] = None
    new_result["mb_confidence"] = 0.0
    new_result["genres"] = []
    new_result["source_name"] = None
    new_result["meta_source_url"] = None

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["release_year"] == old_result["release_year"]
    assert merged["country"] == old_result["country"]
    assert merged["artist_country_tag"] == old_result["artist_country_tag"]
    assert merged["genres"] == old_result["genres"]


def test_merge_prefer_better_clears_source_fields_without_genres():
    old_result = _valid_result()
    old_result["genres"] = []
    old_result["source_name"] = "Discogs"
    old_result["meta_source_url"] = "https://example.com/stale"

    new_result = _valid_result()
    new_result["genres"] = []
    new_result["source_name"] = "Discogs"
    new_result["meta_source_url"] = "https://example.com/new"

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["genres"] == []
    assert merged["source_name"] is None
    assert merged["meta_source_url"] is None


def test_merge_prefer_better_preserves_best_metadata_block_as_unit():
    old_result = _valid_result()
    old_result["genres"] = ["rock", "indie"]
    old_result["source_name"] = "Discogs"
    old_result["meta_source_url"] = "https://example.com/old"

    new_result = _valid_result()
    new_result["release_year"] = None
    new_result["country"] = None
    new_result["artist_country_tag"] = None
    new_result["mb_release_date"] = None
    new_result["mb_confidence"] = 0.0
    new_result["genres"] = []
    new_result["source_name"] = "Wrong Source"
    new_result["meta_source_url"] = "https://example.com/new"

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["genres"] == old_result["genres"]
    assert merged["source_name"] == old_result["source_name"]
    assert merged["meta_source_url"] == old_result["meta_source_url"]


def test_merge_prefer_better_keeps_better_new_genre_block_even_if_old_metadata_wins():
    old_result = _valid_result()
    old_result["genres"] = ["rock"]
    old_result["source_name"] = "Discogs"
    old_result["meta_source_url"] = "https://example.com/old"
    old_result["release_year"] = 2024
    old_result["artist_country_tag"] = "american"
    old_result["mb_release_date"] = "2024-01-01"
    old_result["mb_confidence"] = 0.9

    new_result = _valid_result()
    new_result["genres"] = ["rock", "indie", "experimental", "post-rock"]
    new_result["source_name"] = "Discogs"
    new_result["meta_source_url"] = "https://example.com/new"
    new_result["release_year"] = None
    new_result["artist_country_tag"] = None
    new_result["mb_release_date"] = None
    new_result["mb_confidence"] = 0.0

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["release_year"] == old_result["release_year"]
    assert merged["country"] == old_result["country"]
    assert merged["artist_country_tag"] == old_result["artist_country_tag"]
    assert merged["genres"] == new_result["genres"]
    assert merged["source_name"] == new_result["source_name"]
    assert merged["meta_source_url"] == new_result["meta_source_url"]
