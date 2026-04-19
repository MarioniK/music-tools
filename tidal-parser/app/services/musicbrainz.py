import html
import asyncio
import logging
import re
import time

import httpx
from app import settings
from app import metrics


logger = logging.getLogger("tidal_parser")
_missing_contact_email_warned = False
_musicbrainz_rate_limit_lock = None
_musicbrainz_last_request_started_at = None

COUNTRY_TAG_MAP = {
    "US": "american",
    "USA": "american",
    "UNITED STATES": "american",
    "GB": "british",
    "UK": "british",
    "UNITED KINGDOM": "british",
    "ENGLAND": "british",
    "SCOTLAND": "british",
    "WALES": "british",
    "NORTHERN IRELAND": "british",
    "IE": "irish",
    "IRELAND": "irish",
    "CA": "canadian",
    "CANADA": "canadian",
    "AU": "australian",
    "AUSTRALIA": "australian",
    "NZ": "newzealand",
    "NEW ZEALAND": "newzealand",
    "DE": "german",
    "GERMANY": "german",
    "FR": "french",
    "FRANCE": "french",
    "IT": "italian",
    "ITALY": "italian",
    "ES": "spanish",
    "SPAIN": "spanish",
    "SE": "swedish",
    "SWEDEN": "swedish",
    "NO": "norwegian",
    "NORWAY": "norwegian",
    "DK": "danish",
    "DENMARK": "danish",
    "FI": "finnish",
    "FINLAND": "finnish",
    "IS": "icelandic",
    "ICELAND": "icelandic",
    "NL": "dutch",
    "NETHERLANDS": "dutch",
    "BE": "belgian",
    "BELGIUM": "belgian",
    "CH": "swiss",
    "SWITZERLAND": "swiss",
    "AT": "austrian",
    "AUSTRIA": "austrian",
    "PL": "polish",
    "POLAND": "polish",
    "CZ": "czech",
    "CZECHIA": "czech",
    "CZECH REPUBLIC": "czech",
    "SK": "slovak",
    "SLOVAKIA": "slovak",
    "HU": "hungarian",
    "HUNGARY": "hungarian",
    "RO": "romanian",
    "ROMANIA": "romanian",
    "BG": "bulgarian",
    "BULGARIA": "bulgarian",
    "GR": "greek",
    "GREECE": "greek",
    "TR": "turkish",
    "TURKEY": "turkish",
    "UA": "ukrainian",
    "UKRAINE": "ukrainian",
    "BY": "belarusian",
    "BELARUS": "belarusian",
    "RU": "russian",
    "RUSSIA": "russian",
    "JP": "japanese",
    "JAPAN": "japanese",
    "KR": "korean",
    "SOUTH KOREA": "korean",
    "KOREA, REPUBLIC OF": "korean",
    "CN": "chinese",
    "CHINA": "chinese",
    "TW": "taiwanese",
    "TAIWAN": "taiwanese",
    "HK": "hongkong",
    "HONG KONG": "hongkong",
    "SG": "singaporean",
    "SINGAPORE": "singaporean",
    "BR": "brazilian",
    "BRAZIL": "brazilian",
    "AR": "argentinian",
    "ARGENTINA": "argentinian",
    "MX": "mexican",
    "MEXICO": "mexican",
    "CL": "chilean",
    "CHILE": "chilean",
    "CO": "colombian",
    "COLOMBIA": "colombian",
    "PE": "peruvian",
    "PERU": "peruvian",
    "PT": "portuguese",
    "PORTUGAL": "portuguese",
    "ZA": "southafrican",
    "SOUTH AFRICA": "southafrican",
}

COUNTRY_DISPLAY_MAP = {
    "american": "United States",
    "british": "United Kingdom",
    "irish": "Ireland",
    "canadian": "Canada",
    "australian": "Australia",
    "newzealand": "New Zealand",
    "german": "Germany",
    "french": "France",
    "italian": "Italy",
    "spanish": "Spain",
    "swedish": "Sweden",
    "norwegian": "Norway",
    "danish": "Denmark",
    "finnish": "Finland",
    "icelandic": "Iceland",
    "dutch": "Netherlands",
    "belgian": "Belgium",
    "swiss": "Switzerland",
    "austrian": "Austria",
    "polish": "Poland",
    "czech": "Czechia",
    "slovak": "Slovakia",
    "hungarian": "Hungary",
    "romanian": "Romania",
    "bulgarian": "Bulgaria",
    "greek": "Greece",
    "turkish": "Turkey",
    "ukrainian": "Ukraine",
    "belarusian": "Belarus",
    "russian": "Russia",
    "japanese": "Japan",
    "korean": "South Korea",
    "chinese": "China",
    "taiwanese": "Taiwan",
    "hongkong": "Hong Kong",
    "singaporean": "Singapore",
    "brazilian": "Brazil",
    "argentinian": "Argentina",
    "mexican": "Mexico",
    "chilean": "Chile",
    "colombian": "Colombia",
    "peruvian": "Peru",
    "portuguese": "Portugal",
    "southafrican": "South Africa",
}


def _record_musicbrainz_outcome(outcome):
    if outcome == "success":
        metrics.record_musicbrainz_outcome("success")
    elif outcome == "not_found":
        metrics.record_musicbrainz_outcome("not_found")
    else:
        metrics.record_musicbrainz_outcome("failure")


def clean_text(value):
    if not value:
        return None
    value = html.unescape(str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def build_musicbrainz_user_agent():
    global _missing_contact_email_warned

    contact_email = settings.get_musicbrainz_contact_email()
    if contact_email:
        return "{} ({})".format(settings.get_musicbrainz_app_name(), contact_email)

    if not _missing_contact_email_warned:
        logger.warning(
            "event=musicbrainz_user_agent_config outcome=missing_contact_email source=musicbrainz reason=missing_contact_email"
        )
        _missing_contact_email_warned = True

    return settings.get_musicbrainz_app_name()


def build_musicbrainz_headers():
    return {
        "User-Agent": build_musicbrainz_user_agent(),
        "Accept": "application/json",
    }


def get_musicbrainz_rate_limit_lock():
    global _musicbrainz_rate_limit_lock

    if _musicbrainz_rate_limit_lock is None:
        _musicbrainz_rate_limit_lock = asyncio.Lock()

    return _musicbrainz_rate_limit_lock


async def wait_for_musicbrainz_rate_limit():
    global _musicbrainz_last_request_started_at

    min_interval_s = settings.get_musicbrainz_min_interval_s()
    lock = get_musicbrainz_rate_limit_lock()

    async with lock:
        now = time.monotonic()
        last_started_at = _musicbrainz_last_request_started_at

        if last_started_at is not None:
            wait_s = (last_started_at + min_interval_s) - now
            if wait_s > 0:
                logger.info(
                    "event=musicbrainz_rate_limit outcome=wait source=musicbrainz wait_s=%.3f reason=min_interval",
                    wait_s,
                )
                await asyncio.sleep(wait_s)

        _musicbrainz_last_request_started_at = time.monotonic()


def country_display_from_tag(country_tag):
    if not country_tag:
        return None
    return COUNTRY_DISPLAY_MAP.get(str(country_tag).strip().lower())


def score_similarity(a, b):
    a = (clean_text(a) or "").lower()
    b = (clean_text(b) or "").lower()

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 70

    a_words = set(re.findall(r"[a-z0-9]+", a))
    b_words = set(re.findall(r"[a-z0-9]+", b))
    if not a_words or not b_words:
        return 0

    overlap = len(a_words & b_words)
    total = len(a_words | b_words)
    return int((overlap / float(total)) * 100)


def infer_mb_release_kind(primary_type, secondary_types, entity_type):
    pt = (primary_type or "").lower()
    st = set([str(x).lower() for x in (secondary_types or [])])

    if "ep" in st:
        return "ep"
    if pt == "album":
        return "album"
    if pt == "single":
        return "single"

    return "album" if entity_type == "album" else "single"


async def fetch_musicbrainz_json(url, params):
    headers = build_musicbrainz_headers()
    await wait_for_musicbrainz_rate_limit()

    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


async def fetch_musicbrainz_json_with_retry(url, params, context):
    last_error = None
    last_status_code = None

    max_attempts = settings.get_musicbrainz_max_attempts()
    retry_delay_s = settings.get_musicbrainz_retry_delay_s()

    for attempt in range(1, max_attempts + 1):
        try:
            data = await fetch_musicbrainz_json(url, params)
            return {
                "outcome": "success",
                "data": data,
                "status_code": None,
                "error": None,
            }
        except httpx.TimeoutException as e:
            last_error = e
            if attempt < max_attempts:
                logger.info(
                    "event=musicbrainz_retry outcome=retrying source=musicbrainz context=%s attempt=%d max_attempts=%d reason=timeout",
                    context,
                    attempt,
                    max_attempts,
                )
                await asyncio.sleep(retry_delay_s)
                continue
            return {
                "outcome": "timeout",
                "data": None,
                "status_code": None,
                "error": str(e),
            }
        except httpx.RequestError as e:
            last_error = e
            if attempt < max_attempts:
                logger.info(
                    "event=musicbrainz_retry outcome=retrying source=musicbrainz context=%s attempt=%d max_attempts=%d reason=request_failed",
                    context,
                    attempt,
                    max_attempts,
                )
                await asyncio.sleep(retry_delay_s)
                continue
            return {
                "outcome": "request_failed",
                "data": None,
                "status_code": None,
                "error": str(e),
            }
        except httpx.HTTPStatusError as e:
            last_error = e
            last_status_code = e.response.status_code
            if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                logger.info(
                    "event=musicbrainz_retry outcome=retrying source=musicbrainz context=%s attempt=%d max_attempts=%d reason=http_5xx status_code=%s",
                    context,
                    attempt,
                    max_attempts,
                    e.response.status_code,
                )
                await asyncio.sleep(retry_delay_s)
                continue
            return {
                "outcome": "http_error",
                "data": None,
                "status_code": e.response.status_code,
                "error": str(e),
            }
        except Exception as e:
            last_error = e
            logger.exception(
                "event=musicbrainz_lookup outcome=unexpected_error source=musicbrainz context=%s reason=unexpected_error",
                context,
            )
            break

    return {
        "outcome": "unexpected_error",
        "data": None,
        "status_code": last_status_code,
        "error": str(last_error) if last_error else None,
    }


def _musicbrainz_release_result(
    outcome,
    release_year=None,
    release_date=None,
    release_kind=None,
    artist_id=None,
    confidence=0.0,
):
    return {
        "release_year": release_year,
        "release_date": release_date,
        "release_kind": release_kind,
        "artist_id": artist_id,
        "confidence": confidence,
        "outcome": outcome,
    }


def _extract_country_tag_from_artist_payload(data):
    candidates = []

    if data.get("country"):
        candidates.append(str(data["country"]).upper())

    area = data.get("area")
    if isinstance(area, dict) and area.get("name"):
        candidates.append(str(area["name"]).upper())

    begin_area = data.get("begin-area")
    if isinstance(begin_area, dict) and begin_area.get("name"):
        candidates.append(str(begin_area["name"]).upper())

    for value in candidates:
        if value in COUNTRY_TAG_MAP:
            return COUNTRY_TAG_MAP[value]

    return None


async def get_artist_country_by_mbid_result(artist_id):
    if not artist_id:
        return {"outcome": "not_found", "country_tag": None}

    fetched = await fetch_musicbrainz_json_with_retry(
        "https://musicbrainz.org/ws/2/artist/{}".format(artist_id),
        {"fmt": "json"},
        "artist_country_by_mbid",
    )
    if fetched["outcome"] != "success":
        _record_musicbrainz_outcome(fetched["outcome"])
        logger.warning(
            "event=musicbrainz_lookup outcome=%s source=musicbrainz context=artist_country_by_mbid artist_id=%s",
            fetched["outcome"],
            artist_id,
        )
        return {"outcome": fetched["outcome"], "country_tag": None}

    country_tag = _extract_country_tag_from_artist_payload(fetched["data"])
    outcome = "success" if country_tag else "not_found"
    _record_musicbrainz_outcome(outcome)
    logger.info(
        "event=musicbrainz_lookup outcome=%s source=musicbrainz context=artist_country_by_mbid artist_id=%s",
        outcome,
        artist_id,
    )
    return {"outcome": outcome, "country_tag": country_tag}


async def get_artist_country_by_mbid(artist_id):
    result = await get_artist_country_by_mbid_result(artist_id)
    return result["country_tag"]


async def search_musicbrainz_release_info(artist, title, album, entity_type):
    if entity_type == "album":
        query = 'release:"{}" AND artist:"{}"'.format(title, artist)
        fetched = await fetch_musicbrainz_json_with_retry(
            "https://musicbrainz.org/ws/2/release/",
            {
                "query": query,
                "fmt": "json",
                "limit": 10,
            },
            "release_info_album",
        )
        if fetched["outcome"] != "success":
            _record_musicbrainz_outcome(fetched["outcome"])
            logger.warning(
                "event=musicbrainz_lookup outcome=%s source=musicbrainz context=release_info_album artist=%s title=%s entity_type=%s",
                fetched["outcome"],
                artist,
                title,
                entity_type,
            )
            return _musicbrainz_release_result(fetched["outcome"])

        releases = fetched["data"].get("releases", [])
        if not releases:
            _record_musicbrainz_outcome("not_found")
            logger.info(
                "event=musicbrainz_lookup outcome=not_found source=musicbrainz context=release_info_album artist=%s title=%s entity_type=%s",
                artist,
                title,
                entity_type,
            )
            return _musicbrainz_release_result("not_found")

        scored = []
        for rel in releases:
            rel_title = rel.get("title")
            title_score = score_similarity(title, rel_title)
            artist_score = 0
            artist_id = None

            credits = rel.get("artist-credit", [])
            if credits:
                first = credits[0]
                if isinstance(first, dict):
                    artist_score = score_similarity(artist, first.get("name"))
                    artist_obj = first.get("artist") or {}
                    artist_id = artist_obj.get("id")

            date = rel.get("date")
            year_score = 10 if date and re.match(r"^\d{4}", date) else 0

            total = title_score + artist_score + year_score
            scored.append((total, rel, artist_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best, artist_id = scored[0]

        date = best.get("date")
        year = int(date[:4]) if date and re.match(r"^\d{4}", date) else None
        group = best.get("release-group", {})
        release_kind = infer_mb_release_kind(
            group.get("primary-type"),
            group.get("secondary-types", []),
            entity_type,
        )

        confidence = min(best_score / 200.0, 0.95)
        _record_musicbrainz_outcome("success")
        logger.info(
            "event=musicbrainz_lookup outcome=success source=musicbrainz context=release_info_album artist=%s title=%s entity_type=%s",
            artist,
            title,
            entity_type,
        )
        return _musicbrainz_release_result(
            "success",
            release_year=year,
            release_date=date,
            release_kind=release_kind,
            artist_id=artist_id,
            confidence=confidence,
        )

    query = 'recording:"{}" AND artist:"{}"'.format(title, artist)
    fetched = await fetch_musicbrainz_json_with_retry(
        "https://musicbrainz.org/ws/2/recording/",
        {
            "query": query,
            "fmt": "json",
            "inc": "releases+artist-credits",
            "limit": 10,
        },
        "release_info_recording",
    )
    if fetched["outcome"] != "success":
        _record_musicbrainz_outcome(fetched["outcome"])
        logger.warning(
            "event=musicbrainz_lookup outcome=%s source=musicbrainz context=release_info_recording artist=%s title=%s entity_type=%s",
            fetched["outcome"],
            artist,
            title,
            entity_type,
        )
        return _musicbrainz_release_result(fetched["outcome"])

    recordings = fetched["data"].get("recordings", [])
    if not recordings:
        _record_musicbrainz_outcome("not_found")
        logger.info(
            "event=musicbrainz_lookup outcome=not_found source=musicbrainz context=release_info_recording artist=%s title=%s entity_type=%s",
            artist,
            title,
            entity_type,
        )
        return _musicbrainz_release_result("not_found")

    scored_recordings = []

    for rec in recordings:
        title_score = score_similarity(title, rec.get("title"))
        artist_score = 0
        artist_id = None

        credits = rec.get("artist-credit", [])
        if credits:
            first = credits[0]
            if isinstance(first, dict):
                artist_score = score_similarity(artist, first.get("name"))
                artist_obj = first.get("artist") or {}
                artist_id = artist_obj.get("id")

        album_bonus = 0
        best_release = None
        best_release_score = -1

        for rel in rec.get("releases", []):
            rel_title = rel.get("title")
            rel_score = 0

            if album:
                rel_score += score_similarity(album, rel_title)
            else:
                rel_score += 20 if rel_title else 0

            date = rel.get("date")
            if date and re.match(r"^\d{4}", date):
                rel_score += 10

            if rel_score > best_release_score:
                best_release_score = rel_score
                best_release = rel

        if best_release_score > 0:
            album_bonus = best_release_score

        total = title_score + artist_score + album_bonus
        scored_recordings.append((total, rec, best_release, artist_id))

    scored_recordings.sort(key=lambda x: x[0], reverse=True)
    best_score, best_rec, best_release, artist_id = scored_recordings[0]

    if not best_release:
        _record_musicbrainz_outcome("success")
        logger.info(
            "event=musicbrainz_lookup outcome=success source=musicbrainz context=release_info_recording artist=%s title=%s entity_type=%s",
            artist,
            title,
            entity_type,
        )
        return _musicbrainz_release_result(
            "success",
            release_kind="single",
            artist_id=artist_id,
            confidence=min(best_score / 200.0, 0.6),
        )

    date = best_release.get("date")
    year = int(date[:4]) if date and re.match(r"^\d{4}", date) else None
    group = best_release.get("release-group", {})
    release_kind = infer_mb_release_kind(
        group.get("primary-type"),
        group.get("secondary-types", []),
        entity_type,
    )

    confidence = min(best_score / 220.0, 0.95)

    if confidence < 0.65:
        release_kind = "single"

    _record_musicbrainz_outcome("success")
    logger.info(
        "event=musicbrainz_lookup outcome=success source=musicbrainz context=release_info_recording artist=%s title=%s entity_type=%s",
        artist,
        title,
        entity_type,
    )
    return _musicbrainz_release_result(
        "success",
        release_year=year,
        release_date=date,
        release_kind=release_kind,
        artist_id=artist_id,
        confidence=confidence,
    )


async def search_artist_country_tag(artist, artist_id=None):
    if artist_id:
        country_result = await get_artist_country_by_mbid_result(artist_id)
        if country_result["outcome"] == "success":
            return country_result["country_tag"]
        if country_result["outcome"] != "not_found":
            return None

    if not artist:
        return None

    fetched = await fetch_musicbrainz_json_with_retry(
        "https://musicbrainz.org/ws/2/artist/",
        {
            "query": 'artist:"{}"'.format(artist),
            "fmt": "json",
            "limit": 5,
        },
        "artist_country_search",
    )
    if fetched["outcome"] != "success":
        _record_musicbrainz_outcome(fetched["outcome"])
        logger.warning(
            "event=musicbrainz_lookup outcome=%s source=musicbrainz context=artist_country_search artist=%s",
            fetched["outcome"],
            artist,
        )
        return None

    artists = fetched["data"].get("artists", [])
    if not artists:
        _record_musicbrainz_outcome("not_found")
        logger.info(
            "event=musicbrainz_lookup outcome=not_found source=musicbrainz context=artist_country_search artist=%s",
            artist,
        )
        return None

    best = None
    best_score = -1

    for item in artists:
        score = score_similarity(artist, item.get("name"))
        if score > best_score:
            best_score = score
            best = item

    if not best or best_score < 90:
        _record_musicbrainz_outcome("not_found")
        logger.info(
            "event=musicbrainz_lookup outcome=not_found source=musicbrainz context=artist_country_search artist=%s",
            artist,
        )
        return None

    country_tag = _extract_country_tag_from_artist_payload(best)
    outcome = "success" if country_tag else "not_found"
    _record_musicbrainz_outcome(outcome)
    logger.info(
        "event=musicbrainz_lookup outcome=%s source=musicbrainz context=artist_country_search artist=%s",
        outcome,
        artist,
    )
    return country_tag
