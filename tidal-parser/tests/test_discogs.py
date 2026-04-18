import httpx
import pytest

from app.services import discogs


def test_rank_discogs_candidate_prefers_better_match():
    good = {
        "title": "Artist - Release Title",
        "year": 2024,
        "genre": ["Rock"],
        "style": ["Indie Rock"],
    }
    bad = {
        "title": "Other Artist - Another Release",
        "year": 1999,
        "genre": [],
        "style": [],
    }

    assert discogs.rank_discogs_candidate(good, "Artist", "Release Title") > discogs.rank_discogs_candidate(
        bad,
        "Artist",
        "Release Title",
    )


def test_score_similarity_supports_cyrillic_tokens():
    assert discogs.score_similarity("Молчат Дома", "Молчат Дома") == 100
    assert discogs.score_similarity("Молчат Дома", "Дома") >= 70


def test_normalize_tag_keeps_banned_filtering_after_shared_normalization():
    assert discogs.normalize_tag("Female_Vocalists") is None
    assert discogs.normalize_tag("female-vocalists") is None
    assert discogs.normalize_tag(" Indie-Rock ") == "indie rock"


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_uses_ranked_candidate_and_detail(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        if "database/search" in url:
            return {
                "results": [
                    {
                        "title": "Wrong Artist - Wrong Release",
                        "year": 2001,
                        "genre": ["Rock"],
                        "style": ["Pop"],
                        "uri": "/release/1",
                        "resource_url": "https://api.discogs.com/releases/1",
                    },
                    {
                        "title": "Artist - Release Title",
                        "year": 2024,
                        "genre": ["Rock"],
                        "style": ["Indie Rock"],
                        "uri": "/release/2",
                        "resource_url": "https://api.discogs.com/releases/2",
                    },
                ]
            }

        if url.endswith("/2"):
            return {
                "title": "Release Title",
                "year": 2024,
                "uri": "/release/2",
                "genres": ["Rock"],
                "styles": ["Indie Rock", "Alternative"],
                "artists": [{"name": "Artist"}],
            }

        raise AssertionError("unexpected detail lookup url: {}".format(url))

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == ["rock", "indie rock", "alternative"]
    assert result["meta_source_url"] == "https://www.discogs.com/release/2"
    assert result["note"] is None
    assert result["release_year"] == 2024


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_returns_not_found_for_empty_search(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        return {"results": []}

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert result["note"] == "Discogs не нашёл подходящий релиз."


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_distinguishes_timeout_failure(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        if "database/search" in url:
            return {
                "results": [
                    {
                        "title": "Artist - Release Title",
                        "year": 2024,
                        "uri": "/release/2",
                        "resource_url": "https://api.discogs.com/releases/2",
                    }
                ]
            }

        raise httpx.TimeoutException("timeout")

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert "Таймаут detail lookup Discogs" in result["note"]


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_distinguishes_timeout_on_search(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        raise httpx.TimeoutException("search timeout")

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert "Таймаут запроса к Discogs" in result["note"]


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_distinguishes_http_error(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        request = httpx.Request("GET", url)
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert "HTTP ошибка Discogs" in result["note"]


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_distinguishes_unexpected_error(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        raise RuntimeError("boom")

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert "Неожиданная ошибка Discogs" in result["note"]


@pytest.mark.asyncio
async def test_search_discogs_release_metadata_rejects_detail_mismatch(monkeypatch):
    async def fake_fetch_json(url, params, headers=None):
        if "database/search" in url:
            return {
                "results": [
                    {
                        "title": "Artist - Release Title",
                        "year": 2024,
                        "uri": "/release/2",
                        "resource_url": "https://api.discogs.com/releases/2",
                    }
                ]
            }

        return {
            "title": "Completely Different",
            "year": 2024,
            "uri": "/release/2",
            "genres": ["Rock"],
            "styles": ["Indie Rock"],
            "artists": [{"name": "Other Artist"}],
        }

    monkeypatch.setenv("DISCOGS_TOKEN", "token")
    monkeypatch.setattr(discogs, "fetch_json", fake_fetch_json)

    result = await discogs.search_discogs_release_metadata("Artist", "Release Title")

    assert result["genres"] == []
    assert result["note"] == "Discogs нашёл кандидата, но detail lookup не подтвердил совпадение релиза."
