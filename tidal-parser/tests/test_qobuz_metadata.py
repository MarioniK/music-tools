import pytest
from urllib.parse import parse_qs, urlparse

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


def test_parse_qobuz_release_identity_from_html_uses_json_ld():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "MusicAlbum",
          "name": "The Afterparty",
          "byArtist": {"@type": "MusicGroup", "name": "Lykke Li"},
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


def test_extract_qobuz_release_identity_uses_open_qobuz_candidate_url(monkeypatch):
    def fake_fetch_html(url):
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
        )

    monkeypatch.setattr(qobuz_metadata, "_fetch_qobuz_html", fake_fetch_html)

    result = extract_qobuz_release_identity("https://open.qobuz.com/album/dqqfml14w232y")

    assert result["input_state"] == "extracted_release_identity"
    assert result["source_url"] == "https://open.qobuz.com/album/dqqfml14w232y"
    assert result["qobuz_album_id"] == "dqqfml14w232y"
    assert result["resolved_metadata_url"] in {
        "https://play.qobuz.com/album/dqqfml14w232y",
        "https://www.qobuz.com/album/dqqfml14w232y",
    }
    assert result["artist"] == "Lykke Li"
    assert result["title"] == "The Afterparty"
    assert result["confidence"] == "high"
    assert any("candidate url" in warning.lower() for warning in result["warnings"])


def test_extract_qobuz_release_identity_reports_failed_open_qobuz_candidates(monkeypatch):
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
    assert result["qobuz_album_id"] == "dqqfml14w232y"
    assert result["resolved_metadata_url"] is None
    assert result["title"] is None
    assert result["confidence"] == "low"
    assert any("open qobuz link did not expose release metadata" in warning.lower() for warning in result["warnings"])
    assert any("candidate urls" in warning.lower() for warning in result["warnings"])


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
            "artist": "Lykke Li",
            "title": "The Afterparty",
            "year": 2026,
            "release_date": "2026-01-10",
            "release_type": "album",
            "cover_url": "https://images.qobuz.com/cover.jpg",
            "extraction_method": "json_ld",
            "confidence": "high",
            "warnings": [],
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
        url="https://www.qobuz.com/us-en/album/example/abc",
        force_refresh="0",
        audio=None,
    )

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Qobuz identity" in body
    assert "Lykke Li" in body
    assert "The Afterparty" in body
    assert "2026-01-10" in body
    assert "json_ld" in body


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
