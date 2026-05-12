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


def test_extract_open_qobuz_album_id_basic():
    assert extract_open_qobuz_album_id("https://open.qobuz.com/album/dqqfml14w232y") == "dqqfml14w232y"


def test_extract_open_qobuz_album_id_with_query_and_trailing_slash():
    assert extract_open_qobuz_album_id("https://open.qobuz.com/album/dqqfml14w232y/?x=1") == "dqqfml14w232y"


def test_extract_open_qobuz_album_id_rejects_non_open_host():
    assert extract_open_qobuz_album_id("https://www.qobuz.com/album/dqqfml14w232y") is None


def test_extract_open_qobuz_album_id_rejects_non_album_path():
    assert extract_open_qobuz_album_id("https://open.qobuz.com/track/abc") is None


def test_extract_open_qobuz_track_id_basic():
    assert qobuz_metadata.extract_open_qobuz_track_id("https://open.qobuz.com/track/375049574") == "375049574"


def test_extract_open_qobuz_track_id_with_query_and_trailing_slash():
    assert qobuz_metadata.extract_open_qobuz_track_id("https://open.qobuz.com/track/375049574/?x=1") == "375049574"


def test_extract_open_qobuz_track_id_rejects_non_open_host():
    assert qobuz_metadata.extract_open_qobuz_track_id("https://www.qobuz.com/track/375049574") is None


def test_extract_open_qobuz_track_id_rejects_non_track_path():
    assert qobuz_metadata.extract_open_qobuz_track_id("https://open.qobuz.com/album/abc") is None


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
async def test_parse_form_qobuz_track_url_renders_track_id_notice(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "confidence": "low",
            "warnings": [],
            "qobuz_track_id": "375049574",
            "tidal_search_url": None,
        },
    )

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://open.qobuz.com/track/375049574",
        force_refresh="0",
        audio=None,
    )

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
async def test_parse_form_qobuz_url_renders_extracted_identity(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
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
        },
    )

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
        force_refresh="0",
        audio=None,
    )

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
    assert "Найди Qobuz review по этому релизу." in body
    assert "Не ищи Qobuz review по этому релизу." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_tidal_candidates(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
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
        },
    )

    async def fake_lookup(artist, title, release_type=None, year=None):
        assert artist == "Sepultura"
        assert title == "Nation"
        assert release_type == "album"
        assert year == 2001
        return {
            "state": "success",
            "message": None,
            "query": "Sepultura Nation",
            "release_type": "album",
            "candidates": [
                {
                    "id": "1108027",
                    "type": "album",
                    "title": "Chaos A.D.",
                    "release_date": "1993-01-01",
                    "year": "1993",
                    "tidal_url": "https://tidal.com/album/1108027",
                    "display_line": "Chaos A.D. (1993-01-01) [album]",
                }
            ],
        }

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
        force_refresh="0",
        audio=None,
    )

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
async def test_parse_form_qobuz_url_renders_tidal_candidate_score_and_best_label(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": "The Lemon Twigs",
            "title": "Look For Your Mind!",
            "year": 2026,
            "release_date": "2026-05-08",
            "release_type": "album",
            "cover_url": "https://images.qobuz.com/cover.jpg",
            "extraction_method": "json_ld",
            "confidence": "high",
            "warnings": [],
            "qobuz_album_id": None,
            "qobuz_track_id": None,
        },
    )

    async def fake_lookup(*args, **kwargs):
        return {
            "state": "success",
            "message": None,
            "query": "The Lemon Twigs Look For Your Mind",
            "release_type": "album",
            "tidal_candidates_best_score": 95,
            "tidal_candidates_best_candidate": {
                "id": "498548519",
                "type": "album",
                "title": "Look For Your Mind!",
                "release_date": "2026-05-08",
                "year": "2026",
                "tidal_url": "https://tidal.com/album/498548519",
                "display_line": "Look For Your Mind! (2026-05-08) [album]",
                "score": 95,
                "score_reasons": ["title exact +60", "year exact +20", "type match +15"],
                "is_best_candidate": True,
            },
            "tidal_candidates_match_state": "strong",
            "candidates": [
                {
                    "id": "498548519",
                    "type": "album",
                    "title": "Look For Your Mind!",
                    "release_date": "2026-05-08",
                    "year": "2026",
                    "tidal_url": "https://tidal.com/album/498548519",
                    "display_line": "Look For Your Mind! (2026-05-08) [album]",
                    "score": 95,
                    "score_reasons": ["title exact +60", "year exact +20", "type match +15"],
                    "is_best_candidate": True,
                },
                {
                    "id": "65483367",
                    "type": "album",
                    "title": "A Dream Is All We Know",
                    "release_date": "2024-06-14",
                    "year": "2024",
                    "tidal_url": "https://tidal.com/album/65483367",
                    "display_line": "A Dream Is All We Know (2024-06-14) [album]",
                    "score": 30,
                    "score_reasons": ["title similarity 0.31 +0", "year mismatch -15", "type match +15"],
                    "is_best_candidate": False,
                },
            ],
        }

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/look-for-your-mind-the-lemon-twigs/dqqfml14w232y",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Лучший кандидат" in body
    assert "Score" in body
    assert "95" in body
    assert "title exact +60" in body
    assert "https://tidal.com/album/498548519" in body
    assert "Кандидаты TIDAL требуют ручной проверки." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_shows_manual_verification_note_for_weak_candidates(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": "The Lemon Twigs",
            "title": "Look For Your Mind!",
            "year": 2026,
            "release_date": "2026-05-08",
            "release_type": "album",
            "cover_url": "https://images.qobuz.com/cover.jpg",
            "extraction_method": "json_ld",
            "confidence": "high",
            "warnings": [],
            "qobuz_album_id": None,
            "qobuz_track_id": None,
        },
    )

    async def fake_lookup(*args, **kwargs):
        return {
            "state": "success",
            "message": None,
            "query": "The Lemon Twigs Look For Your Mind",
            "release_type": "album",
            "tidal_candidates_best_score": 42,
            "tidal_candidates_best_candidate": {
                "id": "65483367",
                "type": "album",
                "title": "A Dream Is All We Know",
                "release_date": "2024-06-14",
                "year": "2024",
                "tidal_url": "https://tidal.com/album/65483367",
                "display_line": "A Dream Is All We Know (2024-06-14) [album]",
                "score": 42,
                "score_reasons": ["title similarity 0.31 +0", "year mismatch -15", "type match +15"],
                "is_best_candidate": True,
            },
            "tidal_candidates_match_state": "weak",
            "candidates": [
                {
                    "id": "65483367",
                    "type": "album",
                    "title": "A Dream Is All We Know",
                    "release_date": "2024-06-14",
                    "year": "2024",
                    "tidal_url": "https://tidal.com/album/65483367",
                    "display_line": "A Dream Is All We Know (2024-06-14) [album]",
                    "score": 42,
                    "score_reasons": ["title similarity 0.31 +0", "year mismatch -15", "type match +15"],
                    "is_best_candidate": True,
                }
            ],
        }

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/look-for-your-mind-the-lemon-twigs/dqqfml14w232y",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Кандидаты TIDAL требуют ручной проверки." in body
    assert "Лучший кандидат" not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_tidal_candidates_error_message(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
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
        },
    )

    async def fake_lookup(*args, **kwargs):
        return {
            "state": "error",
            "message": "Не удалось получить кандидатов TIDAL. Используй ручной поиск.",
            "query": "Sepultura Nation",
            "release_type": "album",
            "candidates": [],
        }

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Кандидаты TIDAL" in body
    assert "Не удалось получить кандидатов TIDAL. Используй ручной поиск." in body
    assert "Copy Music prompt" in body
    assert "Copy release line" in body
    assert "Открыть поиск в TIDAL" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_track_without_identity_does_not_lookup_candidates(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)
    called = {"value": False}

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "confidence": "low",
            "warnings": [],
            "qobuz_album_id": None,
            "qobuz_track_id": "375049574",
        },
    )

    async def fake_lookup(*args, **kwargs):
        called["value"] = True
        raise AssertionError("lookup should not be called for open.qobuz.com/track without identity")

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://open.qobuz.com/track/375049574",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert called["value"] is False
    assert "Кандидаты TIDAL" not in body
    assert "Qobuz track ID" in body
    assert "Поиск страницы Qobuz по track ID отключён" in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_ep_url_renders_qobuz_review_prompt(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": "Sepultura",
            "title": "Nation",
            "year": None,
            "release_date": "2001-03-12",
            "release_type": "ep",
            "cover_url": "https://images.qobuz.com/cover.jpg",
            "extraction_method": "json_ld",
            "confidence": "high",
            "warnings": [],
            "qobuz_album_id": None,
            "qobuz_track_id": None,
        },
    )

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://www.qobuz.com/us-en/album/nation-sepultura/0016861959629",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Qobuz identity" in body
    assert "Найди Qobuz review по этому релизу." in body
    assert "Не ищи Qobuz review по этому релизу." not in body


@pytest.mark.asyncio
async def test_parse_form_qobuz_url_renders_album_id_search_helper(monkeypatch):
    parse_form_handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    monkeypatch.setattr(
        main,
        "extract_qobuz_release_identity",
        lambda url: {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": url,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "confidence": "low",
            "warnings": [],
            "qobuz_album_id": "dqqfml14w232y",
            "qobuz_album_id_search_url": main.build_qobuz_album_id_search_url("dqqfml14w232y"),
            "tidal_search_url": None,
        },
    )

    response = await parse_form_handler(
        main.Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
            }
        ),
        url="https://open.qobuz.com/album/dqqfml14w232y",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Найти страницу Qobuz по album ID" in body
    assert "google.com/search" in body
    assert "site%3Aqobuz.com+%22dqqfml14w232y%22" in body or 'site:qobuz.com "dqqfml14w232y"' in body
    assert "Для поиска в TIDAL нужны исполнитель и название релиза." in body
