import pytest
from starlette.requests import Request

from app import apple_music_metadata
from app import main


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


def _apple_identity(
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
        "provider": "apple_music",
        "provider_label": "Apple Music",
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
        "query": "Apple Music candidate lookup",
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


def test_parse_apple_music_release_identity_from_html_album():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://music.apple.com/us/album/folklore-deluxe-version/1528112358" />
        <meta property="og:title" content="folklore (deluxe version) by Taylor Swift on Apple Music" />
        <meta property="og:url" content="https://music.apple.com/us/album/folklore-deluxe-version/1528112358" />
        <meta property="og:type" content="music.album" />
        <meta name="twitter:title" content="folklore (deluxe version) by Taylor Swift on Apple Music" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "folklore (deluxe version)",
          "datePublished": "2020-07-24",
          "byArtist": [{"@type": "MusicGroup", "name": "Taylor Swift"}]
        }
        </script>
        <title>folklore (deluxe version) by Taylor Swift on Apple Music</title>
      </head>
    </html>
    """

    result = apple_music_metadata.parse_apple_music_release_identity_from_html(
        html,
        "https://music.apple.com/us/album/folklore/1528112358",
        final_url="https://music.apple.com/us/album/folklore-deluxe-version/1528112358",
    )

    assert result["provider"] == "apple_music"
    assert result["artist"] == "Taylor Swift"
    assert result["title"] == "folklore (deluxe version)"
    assert result["year"] == 2020
    assert result["release_date"] == "2020-07-24"
    assert result["release_type"] == "album"
    assert result["provider_item_id"] == "1528112358"
    assert result["canonical_url"] == "https://music.apple.com/us/album/folklore-deluxe-version/1528112358"
    assert result["resolved_metadata_url"] == "https://music.apple.com/us/album/folklore-deluxe-version/1528112358"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_apple_music_release_identity_from_html_track():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://music.apple.com/us/song/cardigan/1524801580" />
        <meta property="og:title" content="cardigan by Taylor Swift on Apple Music" />
        <meta property="og:url" content="https://music.apple.com/us/song/cardigan/1524801580" />
        <meta property="og:type" content="music.song" />
        <meta name="twitter:title" content="cardigan by Taylor Swift on Apple Music" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicComposition",
          "name": "cardigan",
          "datePublished": "2020-07-24"
        }
        </script>
        <title>cardigan by Taylor Swift on Apple Music</title>
      </head>
    </html>
    """

    result = apple_music_metadata.parse_apple_music_release_identity_from_html(
        html,
        "https://music.apple.com/us/song/1524801580",
        final_url="https://music.apple.com/us/song/cardigan/1524801580",
    )

    assert result["provider"] == "apple_music"
    assert result["artist"] == "Taylor Swift"
    assert result["title"] == "cardigan"
    assert result["year"] == 2020
    assert result["release_date"] == "2020-07-24"
    assert result["release_type"] == "track"
    assert result["provider_item_id"] == "1524801580"
    assert result["canonical_url"] == "https://music.apple.com/us/song/cardigan/1524801580"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_apple_music_release_identity_from_album_deeplink_prefers_track_id():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://music.apple.com/by/song/choosin-texas/184493215" />
        <meta property="og:title" content="Choosin' Texas by Ella Langley on Apple Music" />
        <meta property="og:url" content="https://music.apple.com/by/song/choosin-texas/184493215" />
        <meta property="og:type" content="music.song" />
        <meta name="twitter:title" content="Choosin' Texas by Ella Langley on Apple Music" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicComposition",
          "name": "Choosin' Texas",
          "datePublished": "2025-10-17"
        }
        </script>
        <title>Choosin' Texas by Ella Langley on Apple Music</title>
      </head>
    </html>
    """

    result = apple_music_metadata.parse_apple_music_release_identity_from_html(
        html,
        "https://music.apple.com/by/album/choosin-texas/1844932149?i=184493215",
        final_url="https://music.apple.com/by/song/choosin-texas/184493215",
    )

    assert result["release_type"] == "track"
    assert result["provider_item_id"] == "184493215"


def test_parse_apple_music_release_identity_from_html_older_album():
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://music.apple.com/us/album/older/412453578" />
        <meta property="og:title" content="Older by George Michael on Apple Music" />
        <meta property="og:url" content="https://music.apple.com/us/album/older/412453578" />
        <meta property="og:type" content="music.album" />
        <meta name="twitter:title" content="Older by George Michael on Apple Music" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "Older",
          "datePublished": "1996-05-13",
          "byArtist": {"@type": "MusicGroup", "name": "George Michael"}
        }
        </script>
        <title>Older by George Michael on Apple Music</title>
      </head>
    </html>
    """

    result = apple_music_metadata.parse_apple_music_release_identity_from_html(
        html,
        "https://music.apple.com/us/album/older/412453578",
        final_url="https://music.apple.com/us/album/older/412453578",
    )

    assert result["artist"] == "George Michael"
    assert result["title"] == "Older"
    assert result["year"] == 1996
    assert result["release_date"] == "1996-05-13"
    assert result["release_type"] == "album"
    assert result["provider_item_id"] == "412453578"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_apple_music_release_identity_from_html_is_safe_for_generic_page():
    result = apple_music_metadata.parse_apple_music_release_identity_from_html(
        "<html><head><title>Apple Music Web Player</title></head></html>",
        "https://music.apple.com/us/album/folklore/1528112358",
    )

    assert result["provider"] == "apple_music"
    assert result["artist"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert result["warnings"]


def test_extract_apple_music_release_identity_uses_fetch_and_canonical_url(monkeypatch):
    def fake_fetch_html(url):
        return (
            """
            <html>
              <head>
                <link rel="canonical" href="https://music.apple.com/us/song/cardigan/1524801580" />
                <meta property="og:title" content="cardigan by Taylor Swift on Apple Music" />
                <meta property="og:url" content="https://music.apple.com/us/song/cardigan/1524801580" />
                <meta property="og:type" content="music.song" />
                <meta name="twitter:title" content="cardigan by Taylor Swift on Apple Music" />
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "MusicComposition",
                  "name": "cardigan",
                  "datePublished": "2020-07-24"
                }
                </script>
              </head>
            </html>
            """,
            "text/html; charset=utf-8",
            "https://music.apple.com/us/song/cardigan/1524801580",
            ["fetch warning"],
        )

    monkeypatch.setattr(apple_music_metadata, "_fetch_apple_music_html", fake_fetch_html)

    result = apple_music_metadata.extract_apple_music_release_identity("https://music.apple.com/us/song/1524801580")

    assert result["artist"] == "Taylor Swift"
    assert result["title"] == "cardigan"
    assert result["provider_item_id"] == "1524801580"
    assert result["canonical_url"] == "https://music.apple.com/us/song/cardigan/1524801580"
    assert "fetch warning" in result["warnings"]


@pytest.mark.asyncio
async def test_parse_form_apple_music_album_auto_handoffs_to_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-album-handoff"
    captured = {"url": None}

    candidate_url = "https://tidal.com/album/498548519"

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Taylor Swift",
            "folklore (deluxe version)",
            2020,
            "2020-07-24",
            "album",
            "1528112358",
            "https://music.apple.com/us/album/folklore-deluxe-version/1528112358",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "Taylor Swift"
        assert title == "folklore (deluxe version)"
        assert release_type == "album"
        assert year == 2020
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "folklore (deluxe version)",
                    "2020-07-24",
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
            artist="Taylor Swift",
            title="folklore (deluxe version)",
            release_year=2020,
            entity_type="album",
            release_kind="album",
        )

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.apple.com/us/album/folklore/1528112358",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Источник: Apple Music → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body
    assert "Copy Music prompt" in body


@pytest.mark.asyncio
async def test_parse_form_apple_music_track_auto_handoffs_to_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-track-handoff"
    captured = {"url": None}

    candidate_url = "https://tidal.com/track/501234567"

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Taylor Swift",
            "cardigan",
            2020,
            "2020-07-24",
            "track",
            "1524801580",
            "https://music.apple.com/us/song/cardigan/1524801580",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "Taylor Swift"
        assert title == "cardigan"
        assert release_type == "track"
        assert year == 2020
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "501234567",
                    "cardigan",
                    "2020-07-24",
                    "2020",
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
            artist="Taylor Swift",
            title="cardigan",
            release_year=2020,
            entity_type="track",
            release_kind="track",
        )

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.apple.com/us/song/1524801580",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Источник: Apple Music → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body


@pytest.mark.asyncio
async def test_parse_form_apple_music_track_without_candidate_year_uses_apple_specific_handoff(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-track-no-year"
    captured = {"url": None}

    candidate_url = "https://tidal.com/track/501234568"

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Ella Langley",
            "Choosin' Texas",
            2025,
            "2025-10-17",
            "track",
            "184493215",
            "https://music.apple.com/by/song/choosin-texas/184493215",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "Ella Langley"
        assert title == "Choosin' Texas"
        assert release_type == "track"
        assert year == 2025
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "501234568",
                    "Choosin' Texas",
                    None,
                    None,
                    candidate_url,
                    80,
                    candidate_type="track",
                    score_reasons=["title exact +60", "year unavailable +0", "type match +15", "relation match +5"],
                )
            ],
            release_type="track",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        return _tidal_handoff_result(
            url,
            artist="Ella Langley",
            title="Choosin' Texas",
            release_year=2025,
            entity_type="track",
            release_kind="track",
        )

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.apple.com/by/album/choosin-texas/1844932149?i=184493215",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Источник: Apple Music → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body


@pytest.mark.asyncio
async def test_parse_form_apple_music_track_with_ambiguous_tied_candidates_stays_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-track-ambiguous"
    called = {"value": False}

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Ella Langley",
            "Choosin' Texas",
            2025,
            "2025-10-17",
            "track",
            "184493215",
            "https://music.apple.com/by/song/choosin-texas/184493215",
        ),
    )

    async def fake_lookup(*args, **kwargs):
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "501234568",
                    "Choosin' Texas",
                    None,
                    None,
                    "https://tidal.com/track/501234568",
                    80,
                    candidate_type="track",
                ),
                _tidal_candidate(
                    "501234569",
                    "Choosin' Texas",
                    None,
                    None,
                    "https://tidal.com/track/501234569",
                    80,
                    candidate_type="track",
                ),
            ],
            release_type="track",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        called["value"] = True
        raise AssertionError("ambiguous Apple candidates should not auto-handoff")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.apple.com/by/album/choosin-texas/1844932149?i=184493215",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Apple Music identity" in body
    assert "Provider ID:" in body
    assert "Источник: Apple Music → TIDAL candidate" not in body


@pytest.mark.asyncio
async def test_parse_form_apple_music_weak_candidate_stays_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-weak"
    called = {"value": False}

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Taylor Swift",
            "folklore (deluxe version)",
            2020,
            "2020-07-24",
            "album",
            "1528112358",
            "https://music.apple.com/us/album/folklore-deluxe-version/1528112358",
        ),
    )

    async def fake_lookup(*args, **kwargs):
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "folklore (deluxe version)",
                    "2020-07-24",
                    "2020",
                    "https://tidal.com/album/498548519",
                    42,
                    candidate_type="album",
                    score_reasons=["title similarity 0.31 +0", "type match +15"],
                )
            ],
            release_type="album",
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        called["value"] = True
        raise AssertionError("auto-handoff should not run for weak Apple candidates")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.apple.com/us/album/folklore/1528112358",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Apple Music identity" in body
    assert "Provider ID:" in body
    assert "Кандидаты TIDAL требуют ручной проверки." in body
    assert "Источник: Apple Music → TIDAL candidate" not in body


@pytest.mark.asyncio
async def test_parse_form_apple_music_parse_failure_falls_back_to_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-apple-parse-failure"
    captured = {"url": None}

    candidate_url = "https://tidal.com/album/498548519"

    monkeypatch.setattr(
        main,
        "extract_apple_music_release_identity",
        lambda url: _apple_identity(
            url,
            "Taylor Swift",
            "folklore (deluxe version)",
            2020,
            "2020-07-24",
            "album",
            "1528112358",
            "https://music.apple.com/us/album/folklore-deluxe-version/1528112358",
        ),
    )

    async def fake_lookup(*args, **kwargs):
        return _tidal_lookup_result(
            [
                _tidal_candidate(
                    "498548519",
                    "folklore (deluxe version)",
                    "2020-07-24",
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
        url="https://music.apple.com/us/album/folklore/1528112358",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Apple Music identity" in body
    assert "Лучший кандидат найден, но TIDAL parse не удался. Используй ссылку вручную." in body
    assert "Кандидаты TIDAL" in body
    assert "Открыть поиск в TIDAL" in body


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected_provider",
    [
        ("https://music.yandex.ru/artist/12345", "Yandex Music"),
    ],
)
async def test_parse_form_yandex_remains_unsupported(monkeypatch, url, expected_provider):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-unsupported-{}".format(expected_provider.lower().replace(" ", "-"))

    async def fake_build_result(*args, **kwargs):
        raise AssertionError("unsupported provider should not reach TIDAL build_result")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url=url,
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Неподдерживаемый ввод" in body
    assert expected_provider in body
