import pytest
from starlette.requests import Request

from app import main
from app import spotify_metadata


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


def _spotify_identity(
    url,
    artist,
    title,
    year,
    release_date,
    release_type,
    provider_item_id,
    canonical_url,
):
    return {
        "input_state": "extracted_release_identity",
        "provider": "spotify",
        "provider_label": "Spotify",
        "source_url": url,
        "resolved_metadata_url": canonical_url,
        "canonical_url": canonical_url,
        "provider_item_id": provider_item_id,
        "artist": artist,
        "title": title,
        "year": year,
        "release_date": release_date,
        "release_type": release_type,
        "cover_url": None,
        "extraction_method": "mixed",
        "primary_source": "json_ld",
        "confidence": "high",
        "warnings": [],
    }


def _tidal_candidate(
    candidate_id,
    title,
    release_date,
    year,
    tidal_url,
    score,
    candidate_type="album",
    is_best_candidate=True,
    score_reasons=None,
):
    return {
        "id": candidate_id,
        "type": candidate_type,
        "title": title,
        "release_date": release_date,
        "year": year,
        "source_relation": "tracks" if candidate_type == "track" else "albums",
        "tidal_url": tidal_url,
        "display_line": "{} ({}) [{}]".format(title, release_date or year or "—", candidate_type),
        "score": score,
        "score_reasons": score_reasons or [],
        "is_best_candidate": is_best_candidate,
    }


def _tidal_lookup_result(candidates, release_type):
    best_candidate = candidates[0] if candidates else None
    match_state = "strong" if best_candidate and (best_candidate.get("score") or 0) >= 75 else "weak"
    if not candidates:
        match_state = "empty"

    return {
        "state": "success",
        "message": None,
        "query": "Spotify candidate lookup",
        "release_type": release_type,
        "candidates": candidates,
        "tidal_candidates_best_score": best_candidate.get("score") if best_candidate else None,
        "tidal_candidates_best_candidate": best_candidate,
        "tidal_candidates_match_state": match_state,
    }


def _tidal_handoff_result(url, artist, title, release_year, entity_type, release_kind):
    return {
        "source_url": url,
        "entity_type": entity_type,
        "tidal_id": "498548519",
        "artist": artist,
        "title": title,
        "album": None,
        "release_kind": release_kind,
        "release_year": release_year,
        "country": "—",
        "genres": [],
        "final_genres": [],
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "blog_output": {
            "line1": "{} — «{}»{}".format(
                artist,
                title,
                " ({})".format(release_year) if entity_type != "track" and release_year is not None else "",
            ),
            "line2": "#music #music2026",
        },
        "source_name": "tidal",
        "meta_source_url": url,
        "note": None,
        "from_cache": False,
    }


def test_parse_spotify_release_identity_from_html_album():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj?si=test" />
        <meta property="og:title" content="After Hours - Album by The Weeknd | Spotify" />
        <meta property="og:url" content="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj?si=test" />
        <meta property="og:type" content="music.album" />
        <meta property="og:description" content="Album • The Weeknd • 2020 • 14 songs, 56 min" />
        <meta name="twitter:title" content="After Hours - Album by The Weeknd | Spotify" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "After Hours",
          "datePublished": "2020-03-20",
          "byArtist": {"@type": "MusicGroup", "name": "The Weeknd"}
        }
        </script>
        <title>After Hours - Album by The Weeknd | Spotify</title>
      </head>
    </html>
    """

    result = spotify_metadata.parse_spotify_release_identity_from_html(
        html,
        "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj?si=test",
        final_url="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj?si=test",
    )

    assert result["provider"] == "spotify"
    assert result["artist"] == "The Weeknd"
    assert result["title"] == "After Hours"
    assert result["year"] == 2020
    assert result["release_date"] == "2020-03-20"
    assert result["release_type"] == "album"
    assert result["provider_item_id"] == "4yP0hdKOZPNshxUOjY0cZj"
    assert result["canonical_url"] == "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_spotify_release_identity_from_html_track():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0" />
        <meta property="og:title" content="The Morning" />
        <meta property="og:url" content="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0" />
        <meta property="og:type" content="music.song" />
        <meta property="og:description" content="Song • The Weeknd • 2011 • 5 min 14 sec" />
        <meta name="twitter:title" content="The Morning" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicRecording",
          "name": "The Morning",
          "datePublished": "2011-01-01",
          "byArtist": {"@type": "MusicGroup", "name": "The Weeknd"}
        }
        </script>
        <title>The Morning</title>
      </head>
    </html>
    """

    result = spotify_metadata.parse_spotify_release_identity_from_html(
        html,
        "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
        final_url="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
    )

    assert result["provider"] == "spotify"
    assert result["artist"] == "The Weeknd"
    assert result["title"] == "The Morning"
    assert result["year"] == 2011
    assert result["release_date"] == "2011-01-01"
    assert result["release_type"] == "track"
    assert result["provider_item_id"] == "4jBfUB4kQJCWOrjGLQqhO0"
    assert result["canonical_url"] == "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_spotify_release_identity_from_html_track_artist_from_description():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0" />
        <meta property="og:title" content="The Morning" />
        <meta property="og:url" content="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0" />
        <meta property="og:type" content="music.song" />
        <meta property="og:description" content="Song • The Weeknd • 2011 • 5 min 14 sec" />
        <meta name="description" content="Song • The Weeknd • 2011 • 5 min 14 sec" />
        <title>The Morning</title>
      </head>
    </html>
    """

    result = spotify_metadata.parse_spotify_release_identity_from_html(
        html,
        "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
        final_url="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
    )

    assert result["artist"] == "The Weeknd"
    assert result["title"] == "The Morning"
    assert result["release_type"] == "track"
    assert result["confidence"] in {"medium", "high"}


def test_parse_spotify_release_identity_from_html_is_safe_for_generic_page():
    result = spotify_metadata.parse_spotify_release_identity_from_html(
        "<html><head><title>Spotify</title></head></html>",
        "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
    )

    assert result["provider"] == "spotify"
    assert result["artist"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert result["warnings"]


def test_extract_spotify_release_identity_rejects_unsupported_paths():
    result = spotify_metadata.extract_spotify_release_identity(
        "https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ"
    )

    assert result["provider"] == "spotify"
    assert result["artist"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert result["warnings"]


@pytest.mark.asyncio
async def test_parse_form_spotify_album_auto_handoffs_to_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-spotify-album-handoff"
    captured = {"url": None}

    candidate_url = "https://tidal.com/album/498548519"

    monkeypatch.setattr(
        main,
        "extract_spotify_release_identity",
        lambda url: _spotify_identity(
            url,
            "The Weeknd",
            "After Hours",
            2020,
            "2020-03-20",
            "album",
            "4yP0hdKOZPNshxUOjY0cZj",
            "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "The Weeknd"
        assert title == "After Hours"
        assert release_type == "album"
        assert year == 2020
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "After Hours",
                    "2020-03-20",
                    "2020",
                    candidate_url,
                    100,
                    candidate_type="album",
                    score_reasons=["title exact +60", "year exact +20", "type match +15", "relation match +5"],
                )
            ],
            release_type="album",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        return _tidal_handoff_result(
            url,
            artist="The Weeknd",
            title="After Hours",
            release_year=2020,
            entity_type="album",
            release_kind="album",
        )

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Источник: Spotify → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body


@pytest.mark.asyncio
async def test_parse_form_spotify_track_auto_handoffs_to_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-spotify-track-handoff"
    captured = {"url": None}

    candidate_url = "https://tidal.com/track/123456789"

    monkeypatch.setattr(
        main,
        "extract_spotify_release_identity",
        lambda url: _spotify_identity(
            url,
            "The Weeknd",
            "The Morning",
            2011,
            "2011-01-01",
            "track",
            "4jBfUB4kQJCWOrjGLQqhO0",
            "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "The Weeknd"
        assert title == "The Morning"
        assert release_type == "track"
        assert year == 2011
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "123456789",
                    "The Morning",
                    "2011-01-01",
                    "2011",
                    candidate_url,
                    100,
                    candidate_type="track",
                    score_reasons=["title exact +60", "year exact +20", "type match +15", "relation match +5"],
                )
            ],
            release_type="track",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        return _tidal_handoff_result(
            url,
            artist="The Weeknd",
            title="The Morning",
            release_year=2011,
            entity_type="track",
            release_kind="track",
        )

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Источник: Spotify → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body


@pytest.mark.asyncio
async def test_parse_form_spotify_weak_candidate_stays_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-spotify-weak"
    called = {"value": False}

    monkeypatch.setattr(
        main,
        "extract_spotify_release_identity",
        lambda url: _spotify_identity(
            url,
            "The Weeknd",
            "After Hours",
            2020,
            "2020-03-20",
            "album",
            "4yP0hdKOZPNshxUOjY0cZj",
            "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        ),
    )

    async def fake_lookup(*args, **kwargs):
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "After Hours",
                    "2020-03-20",
                    "2020",
                    "https://tidal.com/album/498548519",
                    40,
                    candidate_type="album",
                    score_reasons=["title similarity 0.31 +0", "type match +15"],
                )
            ],
            release_type="album",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        called["value"] = True
        raise AssertionError("weak Spotify candidate should not auto-handoff")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Spotify identity" in body
    assert "Provider ID:" in body
    assert "Источник: Spotify → TIDAL candidate" not in body


@pytest.mark.asyncio
async def test_parse_form_spotify_parse_failure_falls_back_to_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-spotify-parse-failure"
    captured = {"url": None}

    candidate_url = "https://tidal.com/album/498548519"

    monkeypatch.setattr(
        main,
        "extract_spotify_release_identity",
        lambda url: _spotify_identity(
            url,
            "The Weeknd",
            "After Hours",
            2020,
            "2020-03-20",
            "album",
            "4yP0hdKOZPNshxUOjY0cZj",
            "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        ),
    )

    async def fake_lookup(*args, **kwargs):
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "After Hours",
                    "2020-03-20",
                    "2020",
                    candidate_url,
                    100,
                    candidate_type="album",
                    score_reasons=["title exact +60", "year exact +20", "type match +15", "relation match +5"],
                )
            ],
            release_type="album",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        raise RuntimeError("TIDAL parse failure")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Spotify identity" in body
    assert "Лучший кандидат найден, но TIDAL parse не удался. Используй ссылку вручную." in body
    assert "Кандидаты TIDAL" in body
    assert "Открыть поиск в TIDAL" in body


@pytest.mark.asyncio
async def test_parse_form_spotify_artist_page_remains_unsupported(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-spotify-unsupported"

    async def fake_build_result(*args, **kwargs):
        raise AssertionError("unsupported Spotify path should not reach TIDAL build_result")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Неподдерживаемый ввод" in body
    assert "Spotify" in body
