import pytest
from starlette.requests import Request

from app import main
from app import odesli_metadata


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


def _yandex_identity(
    url,
    artist,
    title,
    release_type,
    provider_item_id,
    album_id=None,
    track_id=None,
    odesli_page_url=None,
    odesli_tidal_url=None,
    confidence="high",
):
    return {
        "input_state": "extracted_release_identity",
        "provider": "yandex_music",
        "provider_label": "Yandex Music",
        "source_url": url,
        "original_url": url,
        "resolved_metadata_url": odesli_page_url,
        "canonical_url": url.split("?", 1)[0],
        "odesli_page_url": odesli_page_url,
        "odesli_tidal_url": odesli_tidal_url,
        "provider_item_id": provider_item_id,
        "yandex_album_id": album_id,
        "yandex_track_id": track_id,
        "artist": artist,
        "title": title,
        "year": None,
        "release_date": None,
        "release_type": release_type,
        "cover_url": "https://example.com/cover.jpg",
        "api_provider": "yandex",
        "entity_unique_id": "YANDEX_TEST",
        "extraction_method": "odesli",
        "primary_source": "odesli",
        "confidence": confidence,
        "warnings": [],
    }


def _tidal_candidate(
    candidate_id,
    title,
    tidal_url,
    score,
    candidate_type="album",
    release_date=None,
    year=None,
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
        "score_reasons": ["test score"],
        "is_best_candidate": True,
    }


def _tidal_lookup_result(candidates, release_type):
    best_candidate = candidates[0] if candidates else None
    match_state = "strong" if best_candidate and (best_candidate.get("score") or 0) >= 95 else "weak"
    if not candidates:
        match_state = "empty"

    return {
        "state": "success",
        "message": None,
        "query": "Yandex candidate lookup",
        "release_type": release_type,
        "candidates": candidates,
        "tidal_candidates_best_score": best_candidate.get("score") if best_candidate else None,
        "tidal_candidates_best_candidate": best_candidate,
        "tidal_candidates_match_state": match_state,
    }


def _tidal_result(url, artist, title, entity_type, release_kind):
    return {
        "source_url": url,
        "entity_type": entity_type,
        "tidal_id": "123456789",
        "artist": artist,
        "title": title,
        "album": None,
        "release_kind": release_kind,
        "release_year": None,
        "country": "—",
        "genres": [],
        "final_genres": [],
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "blog_output": {
            "line1": "{} — «{}»".format(artist, title),
            "line2": "#music",
        },
        "source_name": "tidal",
        "meta_source_url": url,
        "note": None,
        "from_cache": False,
    }


def test_is_supported_yandex_music_url_and_extract_ids():
    track_url = "https://music.yandex.ru/album/33932468/track/132723441?lang=uz"
    album_url = "https://music.yandex.ru/album/31774859?lang=en"
    unsupported_url = "https://music.yandex.ru/artist/12345"

    assert odesli_metadata.is_supported_yandex_music_url(track_url)
    assert odesli_metadata.is_supported_yandex_music_url(album_url)
    assert not odesli_metadata.is_supported_yandex_music_url(unsupported_url)

    track_ids = odesli_metadata.extract_yandex_ids_from_url(track_url)
    album_ids = odesli_metadata.extract_yandex_ids_from_url(album_url)

    assert track_ids["yandex_album_id"] == "33932468"
    assert track_ids["yandex_track_id"] == "132723441"
    assert track_ids["provider_item_id"] == "132723441"
    assert track_ids["release_type"] == "track"

    assert album_ids["yandex_album_id"] == "31774859"
    assert album_ids["yandex_track_id"] is None
    assert album_ids["provider_item_id"] == "31774859"
    assert album_ids["release_type"] == "album"

    assert odesli_metadata.extract_yandex_ids_from_url(unsupported_url) == {}


def test_extract_tidal_url_from_odesli_normalizes_listen_tidal_url():
    payload = {
        "linksByPlatform": {
            "tidal": {
                "url": "https://listen.tidal.com/track/399044602?utm_source=test",
            }
        }
    }

    assert odesli_metadata.extract_tidal_url_from_odesli(payload) == "https://tidal.com/track/399044602"
    assert odesli_metadata.normalize_tidal_url("https://listen.tidal.com/album/12345?foo=bar") == "https://tidal.com/album/12345"


def test_extract_odesli_yandex_identity_maps_track_metadata():
    payload = {
        "entityUniqueId": "YANDEX_SONG::132723441",
        "pageUrl": "https://song.link/ya/132723441",
        "entitiesByUniqueId": {
            "YANDEX_SONG::132723441": {
                "id": "132723441",
                "type": "song",
                "title": "BOLSHIE KURTKI",
                "artistName": "SALUKI, FRIENDLY THUG 52 NGG",
                "thumbnailUrl": "https://example.com/cover.jpg",
                "apiProvider": "yandex",
            }
        },
        "linksByPlatform": {
            "tidal": {"url": "https://listen.tidal.com/track/399044602"}
        },
    }

    result = odesli_metadata.extract_odesli_yandex_identity(
        "https://music.yandex.ru/album/33932468/track/132723441?lang=uz",
        odesli_result={"ok": True, "status": 200, "api_url": "https://api.song.link/v1-alpha.1/links?url=test", "payload": payload, "warnings": []},
    )

    assert result["provider"] == "yandex_music"
    assert result["artist"] == "SALUKI, FRIENDLY THUG 52 NGG"
    assert result["title"] == "BOLSHIE KURTKI"
    assert result["release_type"] == "track"
    assert result["provider_item_id"] == "132723441"
    assert result["yandex_album_id"] == "33932468"
    assert result["yandex_track_id"] == "132723441"
    assert result["odesli_page_url"] == "https://song.link/ya/132723441"
    assert result["odesli_tidal_url"] == "https://tidal.com/track/399044602"
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_extract_odesli_yandex_identity_maps_album_metadata_without_tidal_url():
    payload = {
        "entityUniqueId": "YANDEX_ALBUM::31774859",
        "pageUrl": "https://album.link/ya/31774859",
        "entitiesByUniqueId": {
            "YANDEX_ALBUM::31774859": {
                "id": "31774859",
                "type": "album",
                "title": "Голоса",
                "artistName": "BEARWOLF",
                "thumbnailUrl": "https://example.com/album.jpg",
                "apiProvider": "yandex",
            }
        },
        "linksByPlatform": {
            "yandex": {"url": "https://music.yandex.ru/album/31774859"}
        },
    }

    result = odesli_metadata.extract_odesli_yandex_identity(
        "https://music.yandex.ru/album/31774859?lang=en",
        odesli_result={"ok": True, "status": 200, "api_url": "https://api.song.link/v1-alpha.1/links?url=test", "payload": payload, "warnings": []},
    )

    assert result["provider"] == "yandex_music"
    assert result["artist"] == "BEARWOLF"
    assert result["title"] == "Голоса"
    assert result["release_type"] == "album"
    assert result["provider_item_id"] == "31774859"
    assert result["odesli_page_url"] == "https://album.link/ya/31774859"
    assert result["odesli_tidal_url"] is None
    assert any("tidal url" in warning.lower() for warning in result["warnings"])


def test_extract_odesli_yandex_identity_returns_safe_warning_for_bad_json():
    result = odesli_metadata.extract_odesli_yandex_identity(
        "https://music.yandex.ru/album/31774859?lang=en",
        odesli_result={
            "ok": False,
            "status": 502,
            "api_url": "https://api.song.link/v1-alpha.1/links?url=test",
            "payload": None,
            "warnings": ["boom"],
            "error": "bad",
        },
    )

    assert result["provider"] == "yandex_music"
    assert result["artist"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert result["warnings"]


@pytest.mark.asyncio
async def test_lookup_yandex_tidal_candidates_with_artist_fallback_prefers_normalized_artist(monkeypatch):
    calls = []

    async def fake_run_timed_stage(stage_name, awaitable):
        assert stage_name == "tidal_openapi_candidates"
        return await awaitable

    async def fake_lookup_tidal_candidates(artist, title, release_type=None, year=None):
        calls.append((artist, title, release_type, year))
        if artist == "P!nk":
            return _tidal_lookup_result([], release_type)

        if artist == "Pink":
            candidate = _tidal_candidate(
                "candidate-1",
                "The Truth About Love",
                "https://tidal.com/album/111111",
                80,
                candidate_type="album",
                year=None,
            )
            return _tidal_lookup_result([candidate], release_type)

        raise AssertionError("unexpected artist query: {}".format(artist))

    monkeypatch.setattr(main, "run_timed_stage", fake_run_timed_stage)
    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup_tidal_candidates)

    result = await main._lookup_yandex_tidal_candidates_with_artist_fallback(
        "P!nk",
        "The Truth About Love",
        "album",
        None,
    )

    assert calls == [
        ("P!nk", "The Truth About Love", "album", None),
        ("Pink", "The Truth About Love", "album", None),
    ]
    assert result["candidates"]
    assert result["candidates"][0]["title"] == "The Truth About Love"
    assert result["query_variants"] == [
        {"artist": "P!nk", "title": "The Truth About Love"},
        {"artist": "Pink", "title": "The Truth About Love"},
    ]


@pytest.mark.asyncio
async def test_parse_form_yandex_track_with_direct_tidal_bridge_calls_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-yandex-direct-bridge"

    candidate_url = "https://listen.tidal.com/track/399044602"
    captured = {}

    monkeypatch.setattr(
        main,
        "extract_odesli_yandex_identity",
        lambda url: _yandex_identity(
            url,
            "SALUKI, FRIENDLY THUG 52 NGG",
            "BOLSHIE KURTKI",
            "track",
            "132723441",
            album_id="33932468",
            track_id="132723441",
            odesli_page_url="https://song.link/ya/132723441",
            odesli_tidal_url=candidate_url,
        ),
    )

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        return _tidal_result(
            url,
            "SALUKI, FRIENDLY THUG 52 NGG",
            "BOLSHIE KURTKI",
            "track",
            "track",
        )

    async def forbidden_lookup(*args, **kwargs):
        raise AssertionError("candidates should not be queried when direct TIDAL bridge is available")

    monkeypatch.setattr(main, "build_result", fake_build_result)
    monkeypatch.setattr(main, "lookup_tidal_candidates", forbidden_lookup)

    response = await parse_form_handler(
        request,
        url="https://music.yandex.ru/album/33932468/track/132723441?lang=uz",
        force_refresh="0",
        manual_release_type="auto",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == "https://tidal.com/track/399044602"
    assert "Yandex Music → Odesli → TIDAL" in body
    assert "https://music.yandex.ru/album/33932468/track/132723441?lang=uz" in body
    assert "https://song.link/ya/132723441" in body
    assert "https://tidal.com/track/399044602" in body


@pytest.mark.asyncio
async def test_parse_form_yandex_album_with_metadata_fallback_handoffs_to_tidal_parse(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-yandex-album-handoff"

    candidate_url = "https://tidal.com/album/5255432"
    captured = {}

    monkeypatch.setattr(
        main,
        "extract_odesli_yandex_identity",
        lambda url: _yandex_identity(
            url,
            "BEARWOLF",
            "Голоса",
            "album",
            "31774859",
            album_id="31774859",
            track_id=None,
            odesli_page_url="https://album.link/ya/31774859",
            odesli_tidal_url=None,
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        captured["lookup"] = (artist, title, release_type, year)
        candidate = _tidal_candidate(
            "candidate-1",
            "Голоса",
            candidate_url,
            100,
            candidate_type="album",
            year=None,
        )
        return _tidal_lookup_result([candidate], release_type)

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["build_result_url"] = url
        return _tidal_result(url, "BEARWOLF", "Голоса", "album", "album")

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)
    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.yandex.ru/album/31774859?lang=en",
        force_refresh="0",
        manual_release_type="auto",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["lookup"] == ("BEARWOLF", "Голоса", "album", None)
    assert captured["build_result_url"] == candidate_url
    assert "Yandex Music → Odesli metadata → TIDAL candidate" in body
    assert "https://album.link/ya/31774859" in body
    assert "https://tidal.com/album/5255432" in body


@pytest.mark.asyncio
async def test_parse_form_yandex_album_weak_candidate_stays_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-yandex-album-weak"

    monkeypatch.setattr(
        main,
        "extract_odesli_yandex_identity",
        lambda url: _yandex_identity(
            url,
            "BEARWOLF",
            "Голоса",
            "album",
            "31774859",
            album_id="31774859",
            odesli_page_url="https://album.link/ya/31774859",
        ),
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        candidate = _tidal_candidate(
            "candidate-1",
            "Голоса",
            "https://tidal.com/album/5255432",
            80,
            candidate_type="album",
            year=None,
        )
        return _tidal_lookup_result([candidate], release_type)

    async def forbidden_build_result(*args, **kwargs):
        raise AssertionError("weak candidate should not handoff")

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)
    monkeypatch.setattr(main, "build_result", forbidden_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.yandex.ru/album/31774859?lang=en",
        force_refresh="0",
        manual_release_type="auto",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Yandex Music identity" in body
    assert "Yandex Music metadata получены через Odesli" in body
    assert "Кандидаты TIDAL" in body
    assert "https://album.link/ya/31774859" in body


@pytest.mark.asyncio
async def test_parse_form_yandex_album_with_pink_artist_uses_normalized_lookup_without_changing_display(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-yandex-pink-fallback"

    monkeypatch.setattr(
        main,
        "extract_odesli_yandex_identity",
        lambda url: _yandex_identity(
            url,
            "P!nk",
            "The Truth About Love",
            "album",
            "594538",
            album_id="594538",
            odesli_page_url="https://album.link/ya/594538",
        ),
    )

    calls = []

    async def fake_run_timed_stage(stage_name, awaitable):
        assert stage_name == "tidal_openapi_candidates"
        return await awaitable

    async def fake_lookup_tidal_candidates(artist, title, release_type=None, year=None):
        calls.append((artist, title, release_type, year))
        if artist == "P!nk":
            return _tidal_lookup_result([], release_type)

        if artist == "Pink":
            candidate = _tidal_candidate(
                "candidate-1",
                "The Truth About Love",
                "https://tidal.com/album/222222",
                80,
                candidate_type="album",
                year=None,
            )
            return _tidal_lookup_result([candidate], release_type)

        raise AssertionError("unexpected artist query: {}".format(artist))

    async def forbidden_build_result(*args, **kwargs):
        raise AssertionError("weak candidate should not handoff")

    monkeypatch.setattr(main, "run_timed_stage", fake_run_timed_stage)
    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup_tidal_candidates)
    monkeypatch.setattr(main, "build_result", forbidden_build_result)

    response = await parse_form_handler(
        request,
        url="https://music.yandex.ru/album/594538",
        force_refresh="0",
        manual_release_type="auto",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert calls == [
        ("P!nk", "The Truth About Love", "album", None),
        ("Pink", "The Truth About Love", "album", None),
    ]
    assert "P!nk" in body
    assert "Yandex Music identity" in body
    assert "Кандидаты TIDAL" in body
    assert "Yandex Music → Odesli metadata → TIDAL candidate" not in body


@pytest.mark.asyncio
async def test_parse_form_yandex_odesli_failure_is_safe(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    request = _make_request()
    request.state.request_id = "req-yandex-odesli-failure"

    monkeypatch.setattr(
        main,
        "extract_odesli_yandex_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "yandex_music",
            "provider_label": "Yandex Music",
            "source_url": url,
            "original_url": url,
            "resolved_metadata_url": None,
            "canonical_url": url.split("?", 1)[0],
            "odesli_page_url": None,
            "odesli_tidal_url": None,
            "provider_item_id": "31774859",
            "yandex_album_id": "31774859",
            "yandex_track_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "api_provider": None,
            "entity_unique_id": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": ["Yandex Music metadata не удалось получить через Odesli."],
        },
    )

    async def forbidden_lookup(*args, **kwargs):
        raise AssertionError("lookup should not run without identity")

    monkeypatch.setattr(main, "lookup_tidal_candidates", forbidden_lookup)

    response = await parse_form_handler(
        request,
        url="https://music.yandex.ru/album/31774859?lang=en",
        force_refresh="0",
        manual_release_type="auto",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Yandex Music identity" in body
    assert "Yandex Music metadata не удалось получить через Odesli." in body
    assert "Кандидаты TIDAL" not in body
