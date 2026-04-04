import io
import json
import sqlite3

import pytest
from starlette.datastructures import UploadFile
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

    upload = UploadFile(filename="sample.mp3", file=io.BytesIO(b"audio-bytes"))
    response = await main.parse_form(
        _make_request(),
        url=base_result["source_url"],
        force_refresh="0",
        audio=upload,
    )

    assert response.status_code == 200
    assert save_calls == []
