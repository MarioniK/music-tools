import pytest

from app import main
from app import spotify_metadata
from helpers import patch_build_result, patch_lookup
from helpers import tidal_candidate as _tidal_candidate
from helpers import tidal_handoff_result as _tidal_handoff_result
from helpers import tidal_lookup_result


def _tidal_lookup_result(candidates, release_type):
    return tidal_lookup_result(candidates, release_type, query="Spotify candidate lookup")


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


_AFTER_HOURS = (
    "The Weeknd",
    "After Hours",
    2020,
    "2020-03-20",
    "album",
    "4yP0hdKOZPNshxUOjY0cZj",
    "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj",
)
_THE_MORNING = (
    "The Weeknd",
    "The Morning",
    2011,
    "2011-01-01",
    "track",
    "4jBfUB4kQJCWOrjGLQqhO0",
    "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
)
_AFTER_HOURS_URL = "https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj"
_REASONS_FULL = ["title exact +60", "year exact +20", "type match +15", "relation match +5"]


def _patch_spotify_identity(monkeypatch, identity_args):
    monkeypatch.setattr(
        main,
        "extract_spotify_release_identity",
        lambda url: _spotify_identity(url, *identity_args),
    )


_HANDOFF_CASES = [
    pytest.param(
        _AFTER_HOURS,
        _AFTER_HOURS_URL,
        _tidal_candidate(
            "498548519", "After Hours", "2020-03-20", "2020",
            "https://tidal.com/album/498548519", 100, candidate_type="album", score_reasons=_REASONS_FULL,
        ),
        "album",
        ("The Weeknd", "After Hours", "album", 2020),
        id="album",
    ),
    pytest.param(
        _THE_MORNING,
        "https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0",
        _tidal_candidate(
            "123456789", "The Morning", "2011-01-01", "2011",
            "https://tidal.com/track/123456789", 100, candidate_type="track", score_reasons=_REASONS_FULL,
        ),
        "track",
        ("The Weeknd", "The Morning", "track", 2011),
        id="track",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("identity, url, candidate, release_type, expected_args", _HANDOFF_CASES)
async def test_parse_form_spotify_strong_candidate_auto_handoffs_to_tidal_parse(
    monkeypatch, post_form, identity, url, candidate, release_type, expected_args
):
    artist, title, year, _release_date, entity_type, _item_id, _canonical = identity
    _patch_spotify_identity(monkeypatch, identity)
    patch_lookup(monkeypatch, _tidal_lookup_result([candidate], release_type=release_type), expected_args)
    captured = patch_build_result(
        monkeypatch,
        handoff=lambda handoff_url: _tidal_handoff_result(
            handoff_url,
            artist=artist,
            title=title,
            release_year=year,
            entity_type=entity_type,
            release_kind=entity_type,
        ),
    )

    response = await post_form(url)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate["tidal_url"]
    assert "Источник: Spotify → TIDAL candidate" in body
    assert "Selected TIDAL URL" in body


@pytest.mark.asyncio
async def test_parse_form_spotify_weak_candidate_stays_identity(monkeypatch, post_form):
    candidate = _tidal_candidate(
        "498548519", "After Hours", "2020-03-20", "2020",
        "https://tidal.com/album/498548519", 40, candidate_type="album",
        score_reasons=["title similarity 0.31 +0", "type match +15"],
    )
    _patch_spotify_identity(monkeypatch, _AFTER_HOURS)
    patch_lookup(monkeypatch, _tidal_lookup_result([candidate], release_type="album"))
    captured = patch_build_result(monkeypatch, forbid="weak Spotify candidate should not auto-handoff")

    response = await post_form(_AFTER_HOURS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["called"] is False
    assert "Spotify identity" in body
    assert "Provider ID:" in body
    assert "Источник: Spotify → TIDAL candidate" not in body


@pytest.mark.asyncio
async def test_parse_form_spotify_parse_failure_falls_back_to_identity(monkeypatch, post_form):
    candidate_url = "https://tidal.com/album/498548519"
    candidate = _tidal_candidate(
        "498548519", "After Hours", "2020-03-20", "2020",
        candidate_url, 100, candidate_type="album", score_reasons=_REASONS_FULL,
    )
    _patch_spotify_identity(monkeypatch, _AFTER_HOURS)
    patch_lookup(monkeypatch, _tidal_lookup_result([candidate], release_type="album"))
    captured = patch_build_result(monkeypatch, error=RuntimeError("TIDAL parse failure"))

    response = await post_form(_AFTER_HOURS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == candidate_url
    assert "Spotify identity" in body
    assert "Лучший кандидат найден, но TIDAL parse не удался. Используй ссылку вручную." in body
    assert "Кандидаты TIDAL" in body
    assert "Открыть поиск в TIDAL" in body


@pytest.mark.asyncio
async def test_parse_form_spotify_artist_page_remains_unsupported(monkeypatch, post_form):
    patch_build_result(monkeypatch, forbid="unsupported Spotify path should not reach TIDAL build_result")

    response = await post_form("https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Неподдерживаемый ввод" in body
    assert "Spotify" in body
