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


def _make_request():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
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


@pytest.mark.asyncio
async def test_build_result_ignores_invalid_baseline(monkeypatch):
    computed = _valid_result()
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

    assert result == computed
    assert saved == [computed]


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


def test_merge_prefer_better_does_not_preserve_stale_note():
    old_result = _valid_result()
    old_result["note"] = "stale note"
    old_result["release_year"] = None
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
    new_result["artist_country_tag"] = None
    new_result["mb_release_date"] = None
    new_result["mb_confidence"] = 0.0
    new_result["genres"] = []
    new_result["source_name"] = None
    new_result["meta_source_url"] = None

    merged = main.merge_prefer_better(old_result, new_result)

    assert merged["release_year"] == old_result["release_year"]
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
    assert merged["artist_country_tag"] == old_result["artist_country_tag"]
    assert merged["genres"] == new_result["genres"]
    assert merged["source_name"] == new_result["source_name"]
    assert merged["meta_source_url"] == new_result["meta_source_url"]
