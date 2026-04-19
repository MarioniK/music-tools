import html
import logging
import re

import httpx

from app.genre_normalization import normalize_genre_value
from app import settings
from app import metrics

DISCOGS_RANK_LIMIT = 5

logger = logging.getLogger("tidal_parser")


def _record_discogs_outcome(outcome):
    metrics.record_discogs_outcome(outcome)


def clean_text(value):
    if not value:
        return None
    value = html.unescape(str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_tag(tag):
    tag = normalize_genre_value(tag)
    if not tag:
        return None

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

    if tag in banned:
        return None

    if re.match(r"^\d{2}s$", tag):
        return None

    if re.match(r"^\d{4}$", tag):
        return None

    if len(tag) < 3 or len(tag) > 30:
        return None

    return tag


def unique_clean_tags(tags):
    result = []
    seen = set()

    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result[:8]


def score_similarity(a, b):
    a = (clean_text(a) or "").lower()
    b = (clean_text(b) or "").lower()

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 70

    a_words = set(re.findall(r"[^\W_]+", a, flags=re.UNICODE))
    b_words = set(re.findall(r"[^\W_]+", b, flags=re.UNICODE))
    if not a_words or not b_words:
        return 0

    overlap = len(a_words & b_words)
    total = len(a_words | b_words)
    return int((overlap / float(total)) * 100)


def _parse_search_result_title(raw_title):
    title = clean_text(raw_title)
    if not title:
        return None, None

    parts = title.split(" - ", 1)
    if len(parts) == 2:
        return clean_text(parts[0]), clean_text(parts[1])

    return None, title


def rank_discogs_candidate(candidate, artist, release_title):
    candidate_artist, candidate_title = _parse_search_result_title(candidate.get("title"))

    title_score = score_similarity(release_title, candidate_title or candidate.get("title"))
    artist_score = score_similarity(artist, candidate_artist)
    exact_bonus = 20 if title_score == 100 and artist_score == 100 else 0
    partial_bonus = 10 if title_score >= 70 and artist_score >= 70 else 0

    return title_score + artist_score + exact_bonus + partial_bonus


async def fetch_json(url, params, headers=None):
    req_headers = {
        "User-Agent": settings.get_discogs_user_agent(),
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    async with httpx.AsyncClient(timeout=20, headers=req_headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


def _extract_release_tags(payload):
    raw_tags = []

    for field in ("genres", "styles", "genre", "style"):
        values = payload.get(field, [])
        if isinstance(values, list):
            raw_tags.extend(values)

    return unique_clean_tags(raw_tags)


def _detail_matches_release(payload, artist, release_title):
    detail_title = payload.get("title")
    detail_artist = None

    artists = payload.get("artists", [])
    if artists and isinstance(artists[0], dict):
        detail_artist = clean_text(
            artists[0].get("name")
            or artists[0].get("anv")
            or artists[0].get("sort_name")
        )

    title_score = score_similarity(release_title, detail_title)
    artist_score = score_similarity(artist, detail_artist)

    return title_score >= 70 and artist_score >= 70


async def search_discogs_release_metadata(artist, release_title):
    discogs_token = settings.get_discogs_token()

    if not discogs_token:
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

    headers = {"Authorization": "Discogs token={}".format(discogs_token)}

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
    except httpx.TimeoutException as e:
        _record_discogs_outcome("failure")
        logger.warning(
            "event=discogs_lookup outcome=timeout source=discogs context=search artist=%s release_title=%s reason=timeout error=%s",
            artist,
            release_title,
            e,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Таймаут запроса к Discogs: {}".format(e),
            "release_year": None,
        }
    except httpx.HTTPStatusError as e:
        _record_discogs_outcome("failure")
        logger.warning(
            "event=discogs_lookup outcome=http_error source=discogs context=search artist=%s release_title=%s status_code=%s reason=http_error error=%s",
            artist,
            release_title,
            e.response.status_code,
            e,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "HTTP ошибка Discogs: {}".format(e),
            "release_year": None,
        }
    except Exception as e:
        _record_discogs_outcome("failure")
        logger.exception(
            "event=discogs_lookup outcome=unexpected_error source=discogs context=search artist=%s release_title=%s reason=unexpected_error",
            artist,
            release_title,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Неожиданная ошибка Discogs: {}".format(e),
            "release_year": None,
        }

    results = search_data.get("results", [])
    if not results:
        _record_discogs_outcome("not_found")
        logger.info(
            "event=discogs_lookup outcome=not_found source=discogs context=search artist=%s release_title=%s candidates_count=0",
            artist,
            release_title,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Discogs не нашёл подходящий релиз.",
            "release_year": None,
        }

    ranked_candidates = results[:DISCOGS_RANK_LIMIT]
    ranked_results = sorted(
        ranked_candidates,
        key=lambda item: rank_discogs_candidate(item, artist, release_title),
        reverse=True,
    )
    best = ranked_results[0]
    best_score = rank_discogs_candidate(best, artist, release_title)

    detail_url = best.get("resource_url")
    if not detail_url:
        _record_discogs_outcome("not_found")
        logger.info(
            "event=discogs_lookup outcome=not_found source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s reason=missing_detail_url",
            artist,
            release_title,
            len(ranked_candidates),
            best_score,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Discogs нашёл кандидата, но detail lookup недоступен.",
            "release_year": None,
        }

    try:
        detail = await fetch_json(detail_url, {}, headers=headers)
    except httpx.TimeoutException as e:
        _record_discogs_outcome("failure")
        logger.warning(
            "event=discogs_lookup outcome=timeout source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s reason=timeout error=%s",
            artist,
            release_title,
            len(ranked_candidates),
            best_score,
            e,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Таймаут detail lookup Discogs: {}".format(e),
            "release_year": None,
        }
    except httpx.HTTPStatusError as e:
        _record_discogs_outcome("failure")
        logger.warning(
            "event=discogs_lookup outcome=http_error source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s status_code=%s reason=http_error error=%s",
            artist,
            release_title,
            len(ranked_candidates),
            best_score,
            e.response.status_code,
            e,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "HTTP ошибка detail lookup Discogs: {}".format(e),
            "release_year": None,
        }
    except Exception as e:
        _record_discogs_outcome("failure")
        logger.exception(
            "event=discogs_lookup outcome=unexpected_error source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s reason=unexpected_error",
            artist,
            release_title,
            len(ranked_candidates),
            best_score,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Неожиданная ошибка detail lookup Discogs: {}".format(e),
            "release_year": None,
        }

    detail_validation_passed = _detail_matches_release(detail, artist, release_title)
    if not detail_validation_passed:
        _record_discogs_outcome("not_found")
        logger.info(
            "event=discogs_lookup outcome=not_found source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s reason=detail_mismatch",
            artist,
            release_title,
            len(ranked_candidates),
            best_score,
        )
        return {
            "genres": [],
            "meta_source_url": None,
            "source_name": "Discogs",
            "note": "Discogs нашёл кандидата, но detail lookup не подтвердил совпадение релиза.",
            "release_year": None,
        }

    genres = _extract_release_tags(detail)

    year = detail.get("year")
    if isinstance(year, int) and year <= 0:
        year = None

    source_url = detail.get("uri") or best.get("uri")
    if source_url and source_url.startswith("/"):
        source_url = "https://www.discogs.com{}".format(source_url)

    _record_discogs_outcome("success")
    logger.info(
        "event=discogs_lookup outcome=success source=discogs context=detail artist=%s release_title=%s candidates_count=%d selected_candidate_score=%s",
        artist,
        release_title,
        len(ranked_candidates),
        best_score,
    )

    return {
        "genres": genres,
        "meta_source_url": source_url,
        "source_name": "Discogs",
        "note": None if genres else "Discogs нашёл релиз, но жанры/стили пустые.",
        "release_year": year,
    }
