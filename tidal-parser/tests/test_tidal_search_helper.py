from urllib.parse import parse_qs, urlparse

from app import main


def _extract_search_query(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("q", [None])[0]


def test_build_tidal_search_url_with_artist_title_and_year():
    url = main.build_tidal_search_url("Lykke Li", "The Afterparty", 2026)

    assert url.startswith("https://tidal.com/search")
    assert _extract_search_query(url) == "Lykke Li The Afterparty 2026"


def test_build_tidal_search_url_requires_artist_and_title():
    assert main.build_tidal_search_url(None, "The Afterparty", 2026) is None
    assert main.build_tidal_search_url("Lykke Li", None, 2026) is None
    assert main.build_tidal_search_url("Lykke Li", "", 2026) is None


def test_manual_release_result_includes_tidal_search_url():
    result = main._build_manual_release_result(
        {
            "artist": "Lykke Li",
            "title": "The Afterparty",
            "year": 2026,
            "confidence": "high",
            "warnings": [],
        }
    )

    assert result["tidal_search_query"] == "Lykke Li The Afterparty 2026"
    assert result["tidal_search_url"] is not None
    assert _extract_search_query(result["tidal_search_url"]) == "Lykke Li The Afterparty 2026"


def test_qobuz_identity_result_includes_tidal_search_url_when_identity_exists():
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
        },
    )

    assert result["tidal_search_query"] == "Lykke Li The Afterparty 2026"
    assert result["tidal_search_url"] is not None
    assert _extract_search_query(result["tidal_search_url"]) == "Lykke Li The Afterparty 2026"


def test_qobuz_identity_result_omits_tidal_search_url_without_identity():
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

    assert result["tidal_search_query"] is None
    assert result["tidal_search_url"] is None
