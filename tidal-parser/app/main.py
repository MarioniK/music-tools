import html
import json
import os
import re
import sqlite3
import tempfile
import time
import unicodedata
from pathlib import Path

import httpx
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


APP_DIR = Path("/app")
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "cache.db"

DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "").strip()
AUDIO_CLASSIFIER_URL = os.getenv(
    "AUDIO_CLASSIFIER_URL",
    "http://genre-classifier:8021/classify"
).strip()

DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="TIDAL Parser")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

USER_AGENT = "TIDALParser/1.0 (+local app)"
MUSICBRAINZ_USER_AGENT = "tidal-parser/1.0 (local-app@example.com)"


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


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            {"ok": False, "error": "Слишком много запросов. Подожди немного и попробуй снова."},
            status_code=429,
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": "Слишком много запросов. Подожди немного и попробуй снова.",
        },
        status_code=429,
    )


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parsed_cache (
            cache_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def build_cache_key(url):
    return url.strip().lower()


def get_cached_result(cache_key):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT payload_json FROM parsed_cache WHERE cache_key = ?", (cache_key,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    try:
        payload = json.loads(row["payload_json"])
    except Exception:
        return None

    payload["from_cache"] = True
    return payload


def save_cached_result(result):
    payload = dict(result)
    payload["from_cache"] = False

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO parsed_cache (
            cache_key,
            payload_json,
            created_at
        ) VALUES (?, ?, ?)
        """,
        (
            build_cache_key(result["source_url"]),
            json.dumps(payload, ensure_ascii=False),
            int(time.time()),
        ),
    )
    conn.commit()
    conn.close()


def delete_cached_result(url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM parsed_cache WHERE cache_key = ?", (build_cache_key(url),))
    conn.commit()
    conn.close()


def clean_text(value):
    if not value:
        return None
    value = html.unescape(str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def slugify_for_tag(value):
    value = clean_text(value) or ""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


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


def metadata_quality_score(result):
    score = 0

    if result.get("release_year"):
        score += 30

    if result.get("artist_country_tag"):
        score += 20

    if result.get("release_kind") in ["single", "album", "ep"]:
        score += 15

    if result.get("mb_release_date"):
        score += 10

    genres = result.get("genres") or []
    score += min(len(genres) * 3, 15)

    if result.get("meta_source_url"):
        score += 5

    confidence = result.get("mb_confidence")
    if isinstance(confidence, (int, float)):
        score += int(confidence * 10)

    return score


def merge_prefer_better(old_result, new_result):
    if not old_result:
        return new_result

    old_score = metadata_quality_score(old_result)
    new_score = metadata_quality_score(new_result)

    merged = dict(new_result)

    fields_to_preserve = [
        "release_year",
        "artist_country_tag",
        "release_kind",
        "mb_release_date",
        "mb_confidence",
        "meta_source_url",
        "source_name",
        "note",
    ]

    for field in fields_to_preserve:
        old_value = old_result.get(field)
        new_value = merged.get(field)

        if old_value not in (None, "", [], {}) and new_value in (None, "", [], {}):
            merged[field] = old_value

    if old_result.get("genres") and not merged.get("genres"):
        merged["genres"] = old_result["genres"]

    if old_score > new_score:
        for field in fields_to_preserve:
            if old_result.get(field) not in (None, "", [], {}):
                merged[field] = old_result.get(field)

        if old_result.get("genres"):
            merged["genres"] = old_result["genres"]

    return merged


def extract_tidal_id(url):
    patterns = [
        (r"tidal\.com/(?:browse/)?track/(\d+)", "track"),
        (r"tidal\.com/(?:browse/)?album/(\d+)", "album"),
    ]

    for pattern, entity_type in patterns:
        match = re.search(pattern, url)
        if match:
            return {"type": entity_type, "id": match.group(1)}

    raise ValueError("Не удалось распознать ссылку TIDAL. Нужна ссылка на track или album.")


async def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.text


async def fetch_json(url, params, headers=None):
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    async with httpx.AsyncClient(timeout=20, headers=req_headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


async def fetch_musicbrainz_json(url, params):
    headers = {
        "User-Agent": MUSICBRAINZ_USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


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


def parse_tidal_metadata_from_html(html_text, entity_type):
    soup = BeautifulSoup(html_text, "lxml")

    title = None
    artist = None
    album = None

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        raw = clean_text(og_title["content"])
        if raw:
            m = re.match(r"(.+?) by (.+?) on TIDAL", raw, flags=re.IGNORECASE)
            if m:
                title = clean_text(m.group(1))
                artist = clean_text(m.group(2))
            else:
                parts = raw.split(" - ")
                if len(parts) == 2:
                    artist = clean_text(parts[0])
                    title = clean_text(parts[1])
                else:
                    title = raw

    json_ld_blocks = soup.find_all("script", attrs={"type": "application/ld+json"})
    for block in json_ld_blocks:
        content = block.string or block.text
        if not content:
            continue

        if entity_type == "track" and not album:
            m = re.search(r'"inAlbum"\s*:\s*\{.*?"name"\s*:\s*"([^"]+)"', content, re.S)
            if m:
                album = clean_text(m.group(1))

        if not artist:
            m = re.search(r'"byArtist"\s*:\s*\{.*?"name"\s*:\s*"([^"]+)"', content, re.S)
            if m:
                artist = clean_text(m.group(1))

        if not title:
            m = re.search(r'"name"\s*:\s*"([^"]+)"', content)
            if m:
                title = clean_text(m.group(1))

    return {
        "title": title,
        "artist": artist,
        "album": album,
    }


async def parse_tidal(url):
    info = extract_tidal_id(url)
    html_text = await fetch_html(url)
    data = parse_tidal_metadata_from_html(html_text, info["type"])

    return {
        "source_url": url,
        "entity_type": info["type"],
        "tidal_id": info["id"],
        "artist": data.get("artist"),
        "title": data.get("title"),
        "album": data.get("album"),
    }


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


async def get_artist_country_by_mbid(artist_id):
    if not artist_id:
        return None

    try:
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/artist/{}".format(artist_id),
            {"fmt": "json"},
        )
    except Exception:
        return None

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


async def search_musicbrainz_release_info(artist, title, album, entity_type):
    try:
        if entity_type == "album":
            query = 'release:"{}" AND artist:"{}"'.format(title, artist)
            data = await fetch_musicbrainz_json(
                "https://musicbrainz.org/ws/2/release/",
                {
                    "query": query,
                    "fmt": "json",
                    "limit": 10,
                },
            )

            releases = data.get("releases", [])
            if not releases:
                return {
                    "release_year": None,
                    "release_date": None,
                    "release_kind": None,
                    "artist_id": None,
                    "confidence": 0.0,
                }

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

            return {
                "release_year": year,
                "release_date": date,
                "release_kind": release_kind,
                "artist_id": artist_id,
                "confidence": confidence,
            }

        query = 'recording:"{}" AND artist:"{}"'.format(title, artist)
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/recording/",
            {
                "query": query,
                "fmt": "json",
                "inc": "releases+artist-credits",
                "limit": 10,
            },
        )

        recordings = data.get("recordings", [])
        if not recordings:
            return {
                "release_year": None,
                "release_date": None,
                "release_kind": None,
                "artist_id": None,
                "confidence": 0.0,
            }

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
            return {
                "release_year": None,
                "release_date": None,
                "release_kind": "single",
                "artist_id": artist_id,
                "confidence": min(best_score / 200.0, 0.6),
            }

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

        return {
            "release_year": year,
            "release_date": date,
            "release_kind": release_kind,
            "artist_id": artist_id,
            "confidence": confidence,
        }

    except Exception:
        return {
            "release_year": None,
            "release_date": None,
            "release_kind": None,
            "artist_id": None,
            "confidence": 0.0,
        }


async def search_artist_country_tag(artist, artist_id=None):
    if artist_id:
        country = await get_artist_country_by_mbid(artist_id)
        if country:
            return country

    if not artist:
        return None

    try:
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/artist/",
            {
                "query": 'artist:"{}"'.format(artist),
                "fmt": "json",
                "limit": 5,
            },
        )
    except Exception:
        return None

    artists = data.get("artists", [])
    if not artists:
        return None

    best = None
    best_score = -1

    for item in artists:
        score = score_similarity(artist, item.get("name"))
        if score > best_score:
            best_score = score
            best = item

    if not best or best_score < 90:
        return None

    candidates = []

    if best.get("country"):
        candidates.append(str(best["country"]).upper())

    area = best.get("area")
    if isinstance(area, dict) and area.get("name"):
        candidates.append(str(area["name"]).upper())

    begin_area = best.get("begin-area")
    if isinstance(begin_area, dict) and begin_area.get("name"):
        candidates.append(str(begin_area["name"]).upper())

    for value in candidates:
        if value in COUNTRY_TAG_MAP:
            return COUNTRY_TAG_MAP[value]

    return None


def normalize_audio_genres(raw_genres):
    filtered = [g for g in raw_genres if g.get("prob", 0) >= 0.08]
    tags = [str(g["tag"]).lower() for g in filtered if g.get("tag")]
    tag_set = set(tags)

    result = []

    def add(tag):
        if tag not in result:
            result.append(tag)

    if "indie rock" in tag_set:
        add("indie rock")
    elif "indie" in tag_set and "rock" in tag_set:
        add("indie rock")

    if "experimental rock" in tag_set:
        add("experimental rock")
    elif "experimental" in tag_set and "rock" in tag_set:
        add("experimental rock")

    if "jazz rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "instrumental" in tag_set and "experimental" in tag_set:
        add("avant-jazz")

    if "alternative rock" in tag_set:
        add("alternative rock")
    elif "alternative" in tag_set and "rock" in tag_set:
        add("alternative rock")

    if "instrumental rock" in tag_set:
        add("instrumental rock")
    elif "instrumental" in tag_set and "rock" in tag_set:
        add("instrumental rock")

    if "electronic" in tag_set:
        add("electronic")

    for item in filtered:
        add(str(item["tag"]).lower())

    return result[:8]


def merge_final_genres(release_genres, audio_genres_pretty, entity_type):
    release_set = set(release_genres)
    audio_set = set(audio_genres_pretty)
    result = []

    def add(tag):
        if tag not in result:
            result.append(tag)

    if ("rock" in release_set or "jazz" in release_set) and "jazz rock" in audio_set:
        add("jazz rock")

    if ("rock" in release_set or "experimental" in release_set) and "experimental rock" in audio_set:
        add("experimental rock")

    if ("rock" in release_set or "alternative" in release_set) and "alternative rock" in audio_set:
        add("alternative rock")

    if ("rock" in release_set or "indie" in release_set or "indie rock" in release_set) and "indie rock" in audio_set:
        add("indie rock")

    if ("rock" in release_set or "instrumental" in release_set) and "instrumental rock" in audio_set:
        add("instrumental rock")

    if "electronic" in release_set or "electronic" in audio_set:
        add("electronic")

    if entity_type == "album" and "instrumental rock" in audio_set and "experimental rock" in audio_set:
        add("post-rock")

    for tag in audio_genres_pretty:
        add(tag)

    for tag in release_genres:
        add(tag)

    return result[:6]


def build_blog_output(result):
    artist = clean_text(result.get("artist")) or "Неизвестный исполнитель"
    title = clean_text(result.get("title")) or "Без названия"
    entity_type = result.get("entity_type")
    year = result.get("release_year")
    country_tag = result.get("artist_country_tag")
    final_genres = result.get("final_genres", [])

    artist_tag = slugify_for_tag(artist)
    genre_tags = [slugify_for_tag(g) for g in final_genres if slugify_for_tag(g)]

    tags = ["#music"]

    if year:
        tags.append("#music{}".format(year))

    if artist_tag:
        tags.append("#{}".format(artist_tag))

    if country_tag:
        tags.append("#{}".format(country_tag))

    tags.extend(["#{}".format(g) for g in genre_tags])
    tags.append("#djdrugfm")

    if entity_type == "track":
        if year == 2026:
            tags.append("#dailylist")
        elif isinstance(year, int) and year < 2016:
            tags.append("#nostalgy")

        line1 = "{} — «{}»".format(artist, title)
    else:
        if year:
            line1 = "{} — «{}» ({})".format(artist, title, year)
        else:
            line1 = "{} — «{}»".format(artist, title)

        if year == 2026:
            tags.extend(["#newrelease", "#newalbum"])
        elif isinstance(year, int) and year < 2016:
            tags.extend(["#nostalgie", "#longplay"])
        else:
            tags.append("#longplay")

    tags.append("#омузыке")

    return {"line1": line1, "line2": " ".join(tags)}


def classify_audio_file(file_bytes, filename):
    suffix = Path(filename or "audio.mp3").suffix.lower() or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        temp_path = tmp.name

    try:
        with open(temp_path, "rb") as f:
            response = requests.post(
                AUDIO_CLASSIFIER_URL,
                files={"file": (filename or "audio{}".format(suffix), f)},
                timeout=120,
            )
        response.raise_for_status()
        data = response.json()

        raw = data.get("genres", [])
        pretty = data.get("genres_pretty", [])
        pretty = pretty or normalize_audio_genres(raw)

        return {"raw": raw, "pretty": pretty}
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass


async def compute_result(url):
    info = extract_tidal_id(url)
    tidal_data = await parse_tidal(url)

    release_title = tidal_data.get("title") if info["type"] == "album" else (
        tidal_data.get("album") or tidal_data.get("title")
    )

    discogs_data = await search_discogs_release_metadata(
        tidal_data.get("artist"),
        release_title,
    )

    mb_data = await search_musicbrainz_release_info(
        tidal_data.get("artist"),
        tidal_data.get("title"),
        tidal_data.get("album"),
        tidal_data.get("entity_type"),
    )

    artist_country_tag = await search_artist_country_tag(
        tidal_data.get("artist"),
        mb_data.get("artist_id"),
    )

    release_year = discogs_data.get("release_year")
    if not release_year and mb_data.get("release_year") and mb_data.get("confidence", 0) >= 0.65:
        release_year = mb_data.get("release_year")

    if tidal_data.get("entity_type") == "album":
        release_kind = "album"
        if mb_data.get("release_kind") in ["album", "ep"]:
            release_kind = mb_data.get("release_kind")
    else:
        release_kind = "single"
        if mb_data.get("release_kind") in ["single", "ep"] and mb_data.get("confidence", 0) >= 0.75:
            release_kind = mb_data.get("release_kind")

    result = {
        **tidal_data,
        "genres": discogs_data.get("genres", []),
        "meta_source_url": discogs_data.get("meta_source_url"),
        "source_name": discogs_data.get("source_name"),
        "note": discogs_data.get("note"),
        "release_year": release_year,
        "artist_country_tag": artist_country_tag,
        "release_kind": release_kind,
        "mb_release_date": mb_data.get("release_date"),
        "mb_confidence": mb_data.get("confidence"),
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "final_genres": discogs_data.get("genres", []),
        "audio_note": None,
        "from_cache": False,
    }

    result["blog_output"] = build_blog_output(result)
    return result


async def build_result(url, force_refresh=False, baseline=None):
    cache_key = build_cache_key(url)
    cached = get_cached_result(cache_key)

    if not force_refresh and cached:
        return cached

    previous = baseline or cached
    result = await compute_result(url)
    result = merge_prefer_better(previous, result)

    save_cached_result(result)
    return result


@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": None, "error": None},
    )


@app.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def parse_form(
    request: Request,
    url: str = Form(...),
    force_refresh: str = Form(default="0"),
    audio: UploadFile = File(default=None),
):
    try:
        result = await build_result(url, force_refresh=(force_refresh == "1"))

        if audio and audio.filename:
            audio_bytes = await audio.read()
            if audio_bytes:
                audio_info = classify_audio_file(audio_bytes, audio.filename)
                result["audio_genres_raw"] = audio_info.get("raw", [])
                result["audio_genres_pretty"] = audio_info.get("pretty", [])
                result["final_genres"] = merge_final_genres(
                    result.get("genres", []),
                    result.get("audio_genres_pretty", []),
                    result.get("entity_type"),
                )
                result["blog_output"] = build_blog_output(result)
                result["from_cache"] = False
                result["audio_note"] = None
                save_cached_result(result)
        elif force_refresh == "1":
            result["audio_note"] = "Обновление без кэша не повторяет аудио-анализ. Если нужен новый audio-анализ, загрузи файл заново."

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": result, "error": None},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": None, "error": str(e)},
            status_code=400,
        )


@app.post("/clear-cache")
@limiter.limit("10/minute")
async def clear_cache(request: Request, url: str = Form(...)):
    old_cached = get_cached_result(build_cache_key(url))
    delete_cached_result(url)

    try:
        result = await build_result(url, force_refresh=True, baseline=old_cached)
        result["audio_note"] = "Кэш пересобран безопасно: если свежий матч оказался слабее, сохранены лучшие найденные данные."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": result, "error": None},
        )
    except Exception as e:
        if old_cached:
            old_cached["audio_note"] = "Не удалось безопасно пересобрать кэш. Показан последний хороший результат."
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "result": old_cached, "error": str(e)},
                status_code=400,
            )

        return RedirectResponse(url="/", status_code=303)


@app.get("/api/parse")
@limiter.limit("10/minute")
async def parse_api(request: Request, url: str, force_refresh: int = 0):
    try:
        result = await build_result(url, force_refresh=(force_refresh == 1))
        return {"ok": True, "data": result}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.get("/health")
@limiter.limit("30/minute")
async def health(request: Request):
    return {"ok": True}