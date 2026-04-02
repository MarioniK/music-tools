import html
import os
import re
import unicodedata

import httpx


DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "").strip()
USER_AGENT = "TIDALParser/1.0 (+local app)"


def clean_text(value):
    if not value:
        return None
    value = html.unescape(str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_tag(tag):
    tag = clean_text(tag)
    if not tag:
        return None

    lowered = tag.lower()
    banned = {
        "seen live",
        "favorites",
        "favorite",
        "favourite",
        "beautiful",
        "awesome",
        "albums i own",
        "crates of vinyl",
        "vinyl",
        "favorite songs",
        "favorite tracks",
        "favorite artists",
        "my favorites",
        "my favourite",
        "under 2000 listeners",
        "female vocalists",
        "male vocalists",
        "love",
        "awesome track",
        "good song",
        "party",
    }

    if lowered in banned:
        return None

    if re.match(r"^\d{2}s$", lowered):
        return None

    if re.match(r"^\d{4}$", lowered):
        return None

    if len(lowered) < 3 or len(lowered) > 30:
        return None

    return lowered


def unique_clean_tags(tags):
    result = []
    seen = set()

    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result[:8]


async def fetch_json(url, params, headers=None):
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    async with httpx.AsyncClient(timeout=20, headers=req_headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


async def search_discogs_release_metadata(artist, release_title):
    if not DISCOGS_TOKEN:
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Не задан DISCOGS_TOKEN в .env",
            "release_year": None,
        }

    if not artist or not release_title:
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Недостаточно данных для поиска релиза.",
            "release_year": None,
        }

    headers = {"Authorization": "Discogs token={}".format(DISCOGS_TOKEN)}

    try:
        search_data = await fetch_json(
            "https://api.discogs.com/database/search",
            {
                "artist": artist,
                "release_title": release_title,
                "type": "release",
                "per_page": 10,
                "page": 1,
            },
            headers=headers,
        )
    except Exception as e:
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Ошибка запроса к Discogs: {}".format(e),
            "release_year": None,
        }

    results = search_data.get("results", [])
    if not results:
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Discogs не нашёл подходящий релиз.",
            "release_year": None,
        }

    best = results[0]
    raw_tags = []

    for field in ("genre", "style"):
        values = best.get(field, [])
        if isinstance(values, list):
            raw_tags.extend(values)

    genres = unique_clean_tags(raw_tags)

    year = best.get("year")
    if isinstance(year, int) and year <= 0:
        year = None

    source_url = best.get("uri")
    if source_url and source_url.startswith("/"):
        source_url = "https://www.discogs.com{}".format(source_url)

    return {
        "genres": genres,
        "meta_source_url": source_url,
        "source_name": "Discogs",
        "note": None if genres else "Discogs нашёл релиз, но жанры/стили пустые.",
        "release_year": year,
    }
