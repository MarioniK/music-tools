import pytest
from email.message import Message
from io import BytesIO
from urllib.parse import parse_qs, urlparse
from urllib.error import HTTPError

from app import main
from app import qobuz_metadata
from app.qobuz_metadata import (
    extract_open_qobuz_album_id,
    extract_qobuz_release_identity,
    parse_qobuz_release_identity_from_html,
)


def _extract_query_param(url, name="q"):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get(name, [None])[0]


def _qobuz_identity(**overrides):
    identity = {
        "input_state": "extracted_release_identity",
        "provider": "qobuz",
        "artist": "Sepultura",
        "title": "Nation",
        "year": 2001,
        "release_date": "2001-03-12",
        "release_type": "album",
        "cover_url": "https://images.qobuz.com/cover.jpg",
        "extraction_method": "json_ld",
        "confidence": "high",
        "warnings": [],
        "qobuz_album_id": None,
        "qobuz_track_id": None,
    }
    identity.update(overrides)
    return identity


def _empty_qobuz_identity(**overrides):
    return _qobuz_identity(
        artist=None,
        title=None,
        year=None,
        release_date=None,
        release_type=None,
        cover_url=None,
        extraction_method="none",
        confidence="low",
        **overrides,
    )


def _patch_qobuz_identity(monkeypatch, identity):
    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {**identity, "source_url": url},
    )


def _tidal_candidate(candidate_id, title, release_date, year, score=None, reasons=None, best=None):
    candidate = {
        "id": candidate_id,
        "type": "album",
        "title": title,
        "release_date": release_date,
        "year": year,
        "tidal_url": f"https://tidal.com/album/{candidate_id}",
        "display_line": f"{title} ({release_date}) [album]",
    }
    if score is not None:
        candidate.update({"score": score, "score_reasons": reasons, "is_best_candidate": best})
    return candidate


def _lookup_result(query, candidates, state="success", message=None, **extra):
    return {
        "state": state,
        "message": message,
        "query": query,
        "release_type": "album",
        **extra,
        "candidates": candidates,
    }


def _patch_tidal_lookup(monkeypatch, result):
    async def fake_lookup(*args, **kwargs):
        return result

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)


_LEMON_TWIGS_URL = "https://www.qobuz.com/us-en/album/look-for-your-mind-the-lemon-twigs/dqqfml14w232y"
_LEMON_TWIGS = {
    "artist": "The Lemon Twigs",
    "title": "Look For Your Mind!",
    "year": 2026,
    "release_date": "2026-05-08",
}
_DREAM_REASONS = ["title similarity 0.31 +0", "year mismatch -15", "type match +15"]
_STRONG_REASONS = ["title exact +60", "year exact +20", "type match +15", "relation match +5"]


def _dream_candidate(score, best):
    return _tidal_candidate("65483367", "A Dream Is All We Know", "2024-06-14", "2024", score, _DREAM_REASONS, best)


def _strong_lookup(candidates):
    best = _tidal_candidate("498548519", "Look For Your Mind", "2026-05-08", "2026", 100, _STRONG_REASONS, True)
    return _lookup_result(
        "The Lemon Twigs Look For Your Mind",
        [best, *candidates],
        tidal_candidates_best_score=100,
        tidal_candidates_best_candidate=best,
        tidal_candidates_match_state="strong",
    )


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://open.qobuz.com/album/dqqfml14w232y", "dqqfml14w232y"),
        ("https://open.qobuz.com/album/dqqfml14w232y/?x=1", "dqqfml14w232y"),
        ("https://www.qobuz.com/album/dqqfml14w232y", None),
        ("https://open.qobuz.com/track/abc", None),
    ],
    ids=["basic", "query_and_trailing_slash", "rejects_non_open_host", "rejects_non_album_path"],
)
def test_extract_open_qobuz_album_id(url, expected):
    assert extract_open_qobuz_album_id(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://open.qobuz.com/track/375049574", "375049574"),
        ("https://open.qobuz.com/track/375049574/?x=1", "375049574"),
        ("https://www.qobuz.com/track/375049574", None),
        ("https://open.qobuz.com/album/abc", None),
    ],
    ids=["basic", "query_and_trailing_slash", "rejects_non_open_host", "rejects_non_track_path"],
)
def test_extract_open_qobuz_track_id(url, expected):
    assert qobuz_metadata.extract_open_qobuz_track_id(url) == expected


def test_parse_qobuz_release_identity_from_html_uses_json_ld():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "The Afterparty",
          "byArtist": {"@type": "MusicGroup", "name": {"@type": "Person", "name": "Lykke Li"}},
          "datePublished": "2026-01-10",
          "image": "https://images.qobuz.com/cover.jpg"
        }
        </script>
        <title>Lykke Li - The Afterparty | Qobuz</title>
      </head>
    </html>
    """

    result = parse_qobuz_release_identity_from_html(html, "https://www.qobuz.com/us-en/album/example/abc")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["artist"] == "Lykke Li"
    assert result["title"] == "The Afterparty"
    assert result["year"] == 2026
    assert result["release_date"] == "2026-01-10"
    assert result["release_type"] == "album"
    assert result["cover_url"] == "https://images.qobuz.com/cover.jpg"
    assert result["extraction_method"] in {"json_ld", "mixed"}
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_qobuz_release_identity_from_html_uses_qobuz_title_pattern_for_artist():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "Look For Your Mind!",
          "datePublished": "2026-05-08",
          "image": "https://images.qobuz.com/fallback-cover.jpg"
        }
        </script>
        <title>Look For Your Mind!, The Lemon Twigs - Qobuz</title>
      </head>
    </html>
    """

    result = parse_qobuz_release_identity_from_html(html, "https://www.qobuz.com/us-en/album/look-for-your-mind-the-lemon-twigs/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["artist"] == "The Lemon Twigs"
    assert result["title"] == "Look For Your Mind!"
    assert result["year"] == 2026
    assert result["release_date"] == "2026-05-08"
    assert result["release_type"] == "album"
    assert result["cover_url"] == "https://images.qobuz.com/fallback-cover.jpg"
    assert result["extraction_method"] in {"json_ld", "mixed"}
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_parse_qobuz_release_identity_from_html_uses_url_slug_fallback_for_qobuz_slug():
    html = """
    <html>
      <head>
        <meta property="og:title" content="Qobuz" />
        <meta property="og:image" content="https://images.qobuz.com/generic-cover.jpg" />
        <title>Qobuz</title>
      </head>
    </html>
    """

    result = parse_qobuz_release_identity_from_html(html, "https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["artist"] == "Sepultura"
    assert result["title"] == "Nation"
    assert result["release_date"] is None
    assert result["release_type"] is None
    assert result["cover_url"] == "https://images.qobuz.com/generic-cover.jpg"
    assert result["extraction_method"] in {"open_graph", "mixed"}
    assert result["confidence"] in {"medium", "low"}
    assert any("generic metadata" in warning.lower() for warning in result["warnings"])


def test_parse_qobuz_release_identity_from_html_uses_open_graph_metadata():
    html = """
    <html>
      <head>
        <meta property="og:title" content="Lykke Li - The Afterparty | Qobuz" />
        <meta property="og:image" content="https://images.qobuz.com/og-cover.jpg" />
        <meta property="og:type" content="music.album" />
        <meta property="music:release_date" content="2026-01-10" />
        <title>Ignored title | Qobuz</title>
      </head>
    </html>
    """

    result = parse_qobuz_release_identity_from_html(html, "https://www.qobuz.com/us-en/album/example/abc")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["artist"] == "Lykke Li"
    assert result["title"] == "The Afterparty"
    assert result["year"] == 2026
    assert result["release_date"] == "2026-01-10"
    assert result["release_type"] == "album"
    assert result["cover_url"] == "https://images.qobuz.com/og-cover.jpg"
    assert result["confidence"] in {"medium", "high"}
    assert result["warnings"] == []


def test_extract_qobuz_release_identity_rejects_non_qobuz_hosts():
    result = extract_qobuz_release_identity("https://example.com/music")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["confidence"] == "low"
    assert result["artist"] is None
    assert result["title"] is None
    assert result["warnings"]


def test_extract_qobuz_release_identity_parses_http_error_html_body(monkeypatch):
    html = """
    <html>
      <head>
        <meta property="og:title" content="Qobuz" />
        <meta property="og:image" content="https://images.qobuz.com/generic-cover.jpg" />
        <title>Qobuz</title>
      </head>
    </html>
    """

    headers = Message()
    headers["Content-Type"] = "text/html; charset=utf-8"
    error = HTTPError(
        "https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
        404,
        "Not Found",
        headers,
        BytesIO(html.encode("utf-8")),
    )

    def fake_fetch_html(url):
        raise error

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    assert result["input_state"] == "extracted_release_identity"
    assert result["provider"] == "qobuz"
    assert result["artist"] == "Sepultura"
    assert result["title"] == "Nation"
    assert result["qobuz_album_id"] is None
    assert result["qobuz_track_id"] is None
    assert result["confidence"] in {"medium", "low"}
    assert any("http 404" in warning.lower() for warning in result["warnings"])


def test_parse_qobuz_release_identity_from_html_rejects_generic_open_qobuz_title():
    html = """
    <html>
      <head>
        <title>Open Qobuz</title>
      </head>
    </html>
    """

    result = parse_qobuz_release_identity_from_html(html, "https://open.qobuz.com/album/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert any("generic metadata" in warning.lower() for warning in result["warnings"])


def test_extract_qobuz_release_identity_warns_for_open_qobuz_links(monkeypatch):
    def fake_fetch_html(url):
        return (
            """
            <html>
              <head>
                <title>Open Qobuz</title>
              </head>
            </html>
            """,
            "text/html; charset=utf-8",
            False,
        )

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert any("open qobuz links" in warning.lower() for warning in result["warnings"])
    assert any("generic metadata" in warning.lower() for warning in result["warnings"])


def test_build_qobuz_album_id_search_url_uses_encoded_album_id():
    url = main.build_qobuz_album_id_search_url("dqqfml14w232y")

    assert url.startswith("https://www.google.com/search")
    query = _extract_query_param(url)
    assert query == 'site:qobuz.com "dqqfml14w232y"'
    assert "dqqfml14w232y" in query


def test_qobuz_identity_result_includes_album_id_search_url_without_artist_title():
    result = main._build_qobuz_identity_result(
        {"provider": "qobuz"},
        {
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "confidence": "low",
            "warnings": [],
            "source_url": "https://open.qobuz.com/album/dqqfml14w232y",
            "qobuz_album_id": "dqqfml14w232y",
        },
    )

    assert result["qobuz_album_id_search_url"] is not None
    assert "google.com/search" in result["qobuz_album_id_search_url"]
    assert _extract_query_param(result["qobuz_album_id_search_url"]) == 'site:qobuz.com "dqqfml14w232y"'
    assert result["tidal_search_url"] is None


def test_qobuz_identity_result_includes_both_helpers_when_identity_exists():
    result = main._build_qobuz_identity_result(
        {"provider": "qobuz"},
        {
            "artist": "Lykke Li",
            "title": "The Afterparty",
            "year": 2026,
            "release_date": "2026-01-10",
            "release_type": "album",
            "cover_url": None,
            "extraction_method": "json_ld",
            "confidence": "high",
            "warnings": [],
            "source_url": "https://www.qobuz.com/us-en/album/example/abc",
            "qobuz_album_id": "abc123",
        },
    )

    assert result["tidal_search_url"] is not None
    assert result["qobuz_album_id_search_url"] is not None
    assert "google.com/search" in result["qobuz_album_id_search_url"]
    assert _extract_query_param(result["qobuz_album_id_search_url"]) == 'site:qobuz.com "abc123"'
    assert result.get("qobuz_track_id_search_url") is None


def test_qobuz_identity_result_builds_release_line_without_year():
    result = main._build_qobuz_identity_result(
        {"provider": "qobuz"},
        {
            "artist": "Sepultura",
            "title": "Nation",
            "year": None,
            "release_date": "2001-03-12",
            "release_type": "album",
            "cover_url": None,
            "extraction_method": "mixed",
            "confidence": "medium",
            "warnings": [],
            "source_url": "https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
            "qobuz_album_id": None,
            "qobuz_track_id": None,
        },
    )

    assert result["blog_output"]["line1"] == "Sepultura — «Nation»"
    assert result["tidal_search_url"] is not None
    assert "Sepultura" in result["tidal_search_url"]
    assert "Nation" in result["tidal_search_url"]
    assert "2001" not in result["tidal_search_url"]


def test_extract_qobuz_release_identity_preserves_open_qobuz_track_id(monkeypatch):
    def fake_fetch_html(url):
        return (
            """
            <html>
              <head>
                <title>Open Qobuz</title>
              </head>
            </html>
            """,
            "text/html; charset=utf-8",
            False,
        )

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/track/375049574")

    assert result["input_state"] == "extracted_release_identity"
    assert result["qobuz_track_id"] == "375049574"
    assert result["qobuz_album_id"] is None
    assert result["resolved_metadata_url"] is None
    assert result["artist"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert any("open qobuz" in warning.lower() for warning in result["warnings"])


@pytest.mark.asyncio
async def test_parse_form_qobuz_track_url_renders_track_id_notice(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _empty_qobuz_identity(qobuz_track_id="375049574", tidal_search_url=None))

    response = await post_form("https://open.qobuz.com/track/375049574")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Qobuz track ID" in body
    assert "375049574" in body
    assert "Поиск страницы Qobuz по track ID отключён" in body
    assert "Найти страницу Qobuz по track ID" not in body
    assert "google.com/search" not in body
    assert "Copy Music prompt" not in body
    assert "Copy release line" not in body
    assert "Найди Qobuz review" not in body
    assert "Не ищи Qobuz review" not in body


def test_extract_qobuz_release_identity_uses_open_qobuz_candidate_url(monkeypatch):
    fetch_calls = []

    def fake_fetch_html(url):
        fetch_calls.append(url)
        if url == "https://open.qobuz.com/album/dqqfml14w232y":
            return (
                """
                <html>
                  <head>
                    <title>Open Qobuz</title>
                  </head>
                </html>
                """,
                "text/html; charset=utf-8",
                False,
                "https://open.qobuz.com/album/dqqfml14w232y",
            )

        if url == "https://www.qobuz.com/us-en/album/dqqfml14w232y":
            return (
                """
                <html>
                  <head>
                    <script type="application/ld+json">
                    {
                      "@context": "https://schema.org",
                      "@type": "MusicAlbum",
                      "name": "The Afterparty",
                      "byArtist": {"@type": "MusicGroup", "name": "Lykke Li"},
                      "datePublished": "2026-01-10",
                      "image": "https://images.qobuz.com/candidate-cover.jpg"
                    }
                    </script>
                    <title>Lykke Li - The Afterparty | Qobuz</title>
                  </head>
                </html>
                """,
                "text/html; charset=utf-8",
                False,
                "https://www.qobuz.com/us-en/album/the-afterparty-lykke-li/dqqfml14w232y",
            )

        return (
            """
            <html>
              <head>
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "MusicAlbum",
                  "name": "The Afterparty",
                  "byArtist": {"@type": "MusicGroup", "name": "Lykke Li"},
                  "datePublished": "2026-01-10",
                  "image": "https://images.qobuz.com/candidate-cover.jpg"
                }
                </script>
                <title>Lykke Li - The Afterparty | Qobuz</title>
              </head>
            </html>
            """,
            "text/html; charset=utf-8",
            False,
            url,
        )

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["source_url"] == "https://open.qobuz.com/album/dqqfml14w232y"
    assert result["qobuz_album_id"] == "dqqfml14w232y"
    assert result["resolved_metadata_url"] in {
        "https://www.qobuz.com/us-en/album/the-afterparty-lykke-li/dqqfml14w232y",
    }
    assert result["artist"] == "Lykke Li"
    assert result["title"] == "The Afterparty"
    assert result["confidence"] == "high"
    assert any("candidate url" in warning.lower() for warning in result["warnings"])
    assert fetch_calls == [
        "https://open.qobuz.com/album/dqqfml14w232y",
        "https://www.qobuz.com/us-en/album/dqqfml14w232y",
    ]


def test_extract_qobuz_release_identity_reports_failed_open_qobuz_candidates(monkeypatch):
    fetch_calls = []

    def fake_fetch_html(url):
        fetch_calls.append(url)
        return (
            """
            <html>
              <head>
                <title>Open Qobuz</title>
              </head>
            </html>
            """,
            "text/html; charset=utf-8",
            False,
            url,
        )

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["qobuz_album_id"] == "dqqfml14w232y"
    assert result["resolved_metadata_url"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert any("open qobuz link did not expose release metadata" in warning.lower() for warning in result["warnings"])
    assert any("candidate urls" in warning.lower() for warning in result["warnings"])
    assert fetch_calls == [
        "https://open.qobuz.com/album/dqqfml14w232y",
        "https://www.qobuz.com/us-en/album/dqqfml14w232y",
        "https://www.qobuz.com/gb-en/album/dqqfml14w232y",
    ]


def test_extract_qobuz_release_identity_stops_after_first_successful_locale_candidate(monkeypatch):
    fetch_calls = []

    def fake_fetch_html(url):
        fetch_calls.append(url)
        if url == "https://open.qobuz.com/album/dqqfml14w232y":
            return (
                "<html><head><title>Open Qobuz</title></head></html>",
                "text/html; charset=utf-8",
                False,
                "https://open.qobuz.com/album/dqqfml14w232y",
            )

        if url == "https://www.qobuz.com/us-en/album/dqqfml14w232y":
            return (
                """
                <html>
                  <head>
                    <script type="application/ld+json">
                    {
                      "@context": "https://schema.org",
                      "@type": "MusicAlbum",
                      "name": "The Afterparty",
                      "byArtist": {"@type": "MusicGroup", "name": "Lykke Li"},
                      "datePublished": "2026-01-10",
                      "image": "https://images.qobuz.com/candidate-cover.jpg"
                    }
                    </script>
                    <title>Lykke Li - The Afterparty | Qobuz</title>
                  </head>
                </html>
                """,
                "text/html; charset=utf-8",
                False,
                "https://www.qobuz.com/us-en/album/the-afterparty-lykke-li/dqqfml14w232y",
            )

        raise AssertionError("gb-en fallback should not be called after first success")

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["resolved_metadata_url"] == "https://www.qobuz.com/us-en/album/the-afterparty-lykke-li/dqqfml14w232y"
    assert fetch_calls == [
        "https://open.qobuz.com/album/dqqfml14w232y",
        "https://www.qobuz.com/us-en/album/dqqfml14w232y",
    ]


def test_extract_qobuz_release_identity_continues_on_429_then_uses_second_locale_candidate(monkeypatch):
    fetch_calls = []
    headers = Message()
    headers["Content-Type"] = "text/html; charset=utf-8"
    error = HTTPError(
        "https://www.qobuz.com/us-en/album/dqqfml14w232y",
        429,
        "Too Many Requests",
        headers,
        BytesIO(b"<html><head><title>Rate limited</title></head></html>"),
    )

    def fake_fetch_html(url):
        fetch_calls.append(url)
        if url == "https://open.qobuz.com/album/dqqfml14w232y":
            return (
                "<html><head><title>Open Qobuz</title></head></html>",
                "text/html; charset=utf-8",
                False,
                "https://open.qobuz.com/album/dqqfml14w232y",
            )

        if url == "https://www.qobuz.com/us-en/album/dqqfml14w232y":
            raise error

        if url == "https://www.qobuz.com/gb-en/album/dqqfml14w232y":
            return (
                """
                <html>
                  <head>
                    <script type="application/ld+json">
                    {
                      "@context": "https://schema.org",
                      "@type": "MusicAlbum",
                      "name": "The Afterparty",
                      "byArtist": {"@type": "MusicGroup", "name": "Lykke Li"},
                      "datePublished": "2026-01-10",
                      "image": "https://images.qobuz.com/candidate-cover.jpg"
                    }
                    </script>
                    <title>Lykke Li - The Afterparty | Qobuz</title>
                  </head>
                </html>
                """,
                "text/html; charset=utf-8",
                False,
                "https://www.qobuz.com/gb-en/album/the-afterparty-lykke-li/dqqfml14w232y",
            )

        raise AssertionError("unexpected fetch url")

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["artist"] == "Lykke Li"
    assert result["title"] == "The Afterparty"
    assert result["resolved_metadata_url"] == "https://www.qobuz.com/gb-en/album/the-afterparty-lykke-li/dqqfml14w232y"
    assert any("429" in warning for warning in result["warnings"])
    assert fetch_calls == [
        "https://open.qobuz.com/album/dqqfml14w232y",
        "https://www.qobuz.com/us-en/album/dqqfml14w232y",
        "https://www.qobuz.com/gb-en/album/dqqfml14w232y",
    ]


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_extracted_identity(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _qobuz_identity())

    response = await post_form("https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Qobuz identity" in body
    assert "Sepultura" in body
    assert "Nation" in body
    assert "2001-03-12" in body
    assert "json_ld" in body
    assert "Sepultura — «Nation» (2001)" in body
    assert "Copy Music prompt" in body
    assert "Copy release line" in body
    assert "Правила оформления и источников: по инструкциям проекта" in body
    assert "Найди Qobuz review по этому релизу." not in body
    assert "Не ищи Qobuz review по этому релизу." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_tidal_candidates(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _qobuz_identity())

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "Sepultura"
        assert title == "Nation"
        assert release_type == "album"
        assert year == 2001
        return _lookup_result(
            "Sepultura Nation",
            [_tidal_candidate("1108027", "Chaos A.D.", "1993-01-01", "1993")],
        )

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await post_form("https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Кандидаты TIDAL" in body
    assert "Chaos A.D." in body
    assert "1993-01-01" in body
    assert "album" in body
    assert "https://tidal.com/album/1108027" in body
    assert "Copy Music prompt" in body
    assert "Copy release line" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_tidal_candidate_score_and_best_label(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _qobuz_identity(**_LEMON_TWIGS))
    reasons = ["title exact +60", "year exact +20", "type match +15"]
    best = _tidal_candidate("498548519", "Look For Your Mind!", "2026-05-08", "2026", 95, reasons, True)
    other = _tidal_candidate("65483367", "A Dream Is All We Know", "2024-06-14", "2024", 30, _DREAM_REASONS, False)
    _patch_tidal_lookup(
        monkeypatch,
        _lookup_result(
            "The Lemon Twigs Look For Your Mind",
            [best, other],
            tidal_candidates_best_score=95,
            tidal_candidates_best_candidate=best,
            tidal_candidates_match_state="strong",
        ),
    )

    response = await post_form(_LEMON_TWIGS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Лучший кандидат" in body
    assert "Score" in body
    assert "95" in body
    assert "title exact +60" in body
    assert "https://tidal.com/album/498548519" in body
    assert "Кандидаты TIDAL требуют ручной проверки." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_shows_manual_verification_note_for_weak_candidates(monkeypatch, post_form):
    called = {"value": False}
    _patch_qobuz_identity(monkeypatch, _qobuz_identity(**_LEMON_TWIGS))
    weak = _dream_candidate(42, True)
    _patch_tidal_lookup(
        monkeypatch,
        _lookup_result(
            "The Lemon Twigs Look For Your Mind",
            [weak],
            tidal_candidates_best_score=42,
            tidal_candidates_best_candidate=weak,
            tidal_candidates_match_state="weak",
        ),
    )

    async def fake_build_result(*args, **kwargs):
        called["value"] = True
        raise AssertionError("auto-handoff should not run for weak candidates")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await post_form(_LEMON_TWIGS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Кандидаты TIDAL требуют ручной проверки." in body
    assert "Лучший кандидат" not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_auto_handoffs_to_tidal_parse_for_strong_candidate(monkeypatch, post_form):
    captured = {"url": None}
    _patch_qobuz_identity(monkeypatch, _qobuz_identity(**_LEMON_TWIGS, resolved_metadata_url=_LEMON_TWIGS_URL))
    _patch_tidal_lookup(monkeypatch, _strong_lookup([_dream_candidate(30, False)]))

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        return {
            "source_url": url,
            "entity_type": "album",
            "tidal_id": "498548519",
            "artist": "The Lemon Twigs",
            "title": "Look For Your Mind!",
            "album": None,
            "release_kind": "album",
            "release_year": 2026,
            "country": "—",
            "genres": [],
            "final_genres": [],
            "audio_genres_raw": [],
            "audio_genres_pretty": [],
            "blog_output": {
                "line1": "The Lemon Twigs — «Look For Your Mind!» (2026)",
                "line2": "#music #music2026",
            },
            "source_name": "tidal",
            "meta_source_url": url,
            "note": None,
            "from_cache": False,
        }

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await post_form(_LEMON_TWIGS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == "https://tidal.com/album/498548519"
    assert "Источник: Qobuz → TIDAL candidate" in body
    assert "Qobuz URL:" in body
    assert "Resolved Qobuz metadata URL:" in body
    assert "Selected TIDAL URL:" in body
    assert "Score:" in body
    assert "Показать кандидатов TIDAL" in body
    assert "Лучший кандидат" in body
    assert "Qobuz identity" not in body
    assert "Look For Your Mind!" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_falls_back_when_auto_handoff_parse_fails(monkeypatch, post_form):
    captured = {"url": None}
    _patch_qobuz_identity(monkeypatch, _qobuz_identity(**_LEMON_TWIGS, resolved_metadata_url=_LEMON_TWIGS_URL))
    _patch_tidal_lookup(monkeypatch, _strong_lookup([]))

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        raise RuntimeError("TIDAL parse failure")

    monkeypatch.setattr(main, "build_result", fake_build_result)

    response = await post_form(_LEMON_TWIGS_URL)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert captured["url"] == "https://tidal.com/album/498548519"
    assert "Лучший кандидат найден, но TIDAL parse не удался. Используй ссылку вручную." in body
    assert "Qobuz identity" in body
    assert "Кандидаты TIDAL" in body
    assert "Copy Music prompt" in body
    assert "Copy release line" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_tidal_candidates_error_message(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _qobuz_identity())
    _patch_tidal_lookup(
        monkeypatch,
        _lookup_result(
            "Sepultura Nation",
            [],
            state="error",
            message="Не удалось получить кандидатов TIDAL. Используй ручной поиск.",
        ),
    )

    response = await post_form("https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Кандидаты TIDAL" in body
    assert "Не удалось получить кандидатов TIDAL. Используй ручной поиск." in body
    assert "Copy Music prompt" in body
    assert "Copy release line" in body
    assert "Открыть поиск в TIDAL" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_track_without_identity_does_not_lookup_candidates(monkeypatch, post_form):
    called = {"value": False}
    _patch_qobuz_identity(monkeypatch, _empty_qobuz_identity(qobuz_track_id="375049574"))

    async def fake_lookup(*args, **kwargs):
        called["value"] = True
        raise AssertionError("lookup should not be called for open.qobuz.com/track without identity")

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await post_form("https://open.qobuz.com/track/375049574")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Кандидаты TIDAL" not in body
    assert "Qobuz track ID" in body
    assert "Поиск страницы Qobuz по track ID отключён" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_ep_url_renders_project_data_prompt(monkeypatch, post_form):
    _patch_qobuz_identity(monkeypatch, _qobuz_identity(year=None, release_type="ep"))

    response = await post_form("https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Qobuz identity" in body
    assert "Правила оформления и источников: по инструкциям проекта" in body
    assert "Тип: EP" in body
    assert "Найди Qobuz review по этому релизу." not in body
    assert "Не ищи Qobuz review по этому релизу." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_album_id_search_helper(monkeypatch, post_form):
    _patch_qobuz_identity(
        monkeypatch,
        _empty_qobuz_identity(
            qobuz_album_id="dqqfml14w232y",
            qobuz_album_id_search_url=main.build_qobuz_album_id_search_url("dqqfml14w232y"),
            tidal_search_url=None,
        ),
    )

    response = await post_form("https://open.qobuz.com/album/dqqfml14w232y")

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Найти страницу Qobuz по album ID" in body
    assert "google.com/search" in body
    assert "site%3Aqobuz.com+%22dqqfml14w232y%22" in body or 'site:qobuz.com "dqqfml14w232y"' in body
    assert "Для поиска в TIDAL нужны исполнитель и название релиза." in body
