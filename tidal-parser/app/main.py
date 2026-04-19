import asyncio
import html
import json
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

from app.genre_normalization import (
    genre_to_blog_tag,
    is_allowed_final_genre,
    normalize_audio_prediction_genres,
    normalize_genres,
)
from app.pipeline_logging import logger, run_timed_stage, run_timed_stage_sync
from app import settings
from app import metrics
from app import request_context
from app.services.discogs import search_discogs_release_metadata
from app.services.musicbrainz import (
    country_display_from_tag,
    search_artist_country_tag,
    search_musicbrainz_release_info,
)


APP_DIR = Path("/app")
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "cache.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="TIDAL Parser")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    request_id = request_context.generate_request_id()
    request.state.request_id = request_id
    token = request_context.set_current_request_id(request_id)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_context.reset_current_request_id(token)



@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    request_id = getattr(request.state, "request_id", None)

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            {
                "ok": False,
                "error": "Слишком много запросов. Подожди немного и попробуй снова.",
                "request_id": request_id,
            },
            status_code=429,
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": "Слишком много запросов. Подожди немного и попробуй снова.",
            "error_request_id": request_id,
            "form_url": request.query_params.get("url", ""),
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


class ClientInputError(ValueError):
    pass


def _is_degraded_result(result):
    return bool(clean_text((result or {}).get("note")))


def build_cache_key(url):
    return url.strip().lower()


def _is_valid_cached_payload(payload):
    if not isinstance(payload, dict):
        return False

    if not isinstance(payload.get("source_url"), str) or not payload.get("source_url").strip():
        return False

    if not isinstance(payload.get("entity_type"), str) or not payload.get("entity_type").strip():
        return False

    if not isinstance(payload.get("tidal_id"), (str, int)):
        return False

    for field in ("genres", "audio_genres_raw", "audio_genres_pretty", "final_genres"):
        value = payload.get(field)
        if value is not None and not isinstance(value, list):
            return False

    blog_output = payload.get("blog_output")
    if blog_output is not None and not isinstance(blog_output, dict):
        return False

    return True


def _normalize_country_fields(result):
    if not isinstance(result, dict):
        return result

    country_tag = result.get("artist_country_tag")
    country = result.get("country")

    if not country and country_tag:
        country = country_display_from_tag(country_tag)

    result["country"] = country
    result["artist_country_tag"] = country_tag
    result.pop("country_tag", None)
    return result


def _build_cache_payload(result):
    payload = _normalize_country_fields(dict(result))
    payload["blog_output"] = build_blog_output(payload)
    payload.pop("from_cache", None)
    payload.pop("audio_note", None)
    return payload


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

    if not _is_valid_cached_payload(payload):
        return None

    payload = _normalize_country_fields(payload)
    payload["blog_output"] = build_blog_output(payload)
    payload["from_cache"] = True
    return payload


def save_cached_result(result):
    payload = _build_cache_payload(result)

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
    score = _genre_metadata_quality_score(result)

    if result.get("release_year"):
        score += 30

    if result.get("artist_country_tag"):
        score += 20

    if result.get("release_kind") in ["single", "album", "ep"]:
        score += 15

    if result.get("mb_release_date"):
        score += 10

    confidence = result.get("mb_confidence")
    if isinstance(confidence, (int, float)):
        score += int(confidence * 10)

    return score


def _genre_metadata_quality_score(result):
    score = 0
    genres = result.get("genres") or []
    if genres:
        score += min(len(genres) * 3, 15)

        if result.get("meta_source_url"):
            score += 5

    return score


def _apply_genre_metadata_block(target, source):
    genres = source.get("genres") or []
    if genres:
        target["genres"] = genres
        target["source_name"] = source.get("source_name")
        target["meta_source_url"] = source.get("meta_source_url")
    else:
        target["genres"] = []
        target["source_name"] = None
        target["meta_source_url"] = None


def merge_prefer_better(old_result, new_result):
    if not old_result:
        return _normalize_country_fields(new_result)

    old_result = _normalize_country_fields(dict(old_result))
    new_result = _normalize_country_fields(dict(new_result))

    old_score = metadata_quality_score(old_result)
    new_score = metadata_quality_score(new_result)
    old_genre_score = _genre_metadata_quality_score(old_result)
    new_genre_score = _genre_metadata_quality_score(new_result)

    merged = dict(new_result)

    fields_to_preserve = [
        "release_year",
        "country",
        "artist_country_tag",
        "release_kind",
        "mb_release_date",
        "mb_confidence",
    ]

    for field in fields_to_preserve:
        old_value = old_result.get(field)
        new_value = merged.get(field)

        if old_value not in (None, "", [], {}) and new_value in (None, "", [], {}):
            merged[field] = old_value

    if old_result.get("genres") and not merged.get("genres"):
        _apply_genre_metadata_block(merged, old_result)
    elif not merged.get("genres"):
        merged["source_name"] = None
        merged["meta_source_url"] = None

    if old_score > new_score:
        for field in fields_to_preserve:
            if old_result.get(field) not in (None, "", [], {}):
                merged[field] = old_result.get(field)

        if old_genre_score > new_genre_score:
            _apply_genre_metadata_block(merged, old_result)

    if not merged.get("genres"):
        merged["source_name"] = None
        merged["meta_source_url"] = None

    return _normalize_country_fields(merged)


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


def validate_user_input_url(url):
    normalized = (url or "").strip()
    if not normalized:
        raise ClientInputError("Нужна ссылка TIDAL на track или album.")

    try:
        extract_tidal_id(normalized)
    except ValueError as e:
        raise ClientInputError(str(e))

    return normalized


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


def _fill_missing_fields(target, source):
    for field in ("title", "artist", "album"):
        if not target.get(field) and source.get(field):
            target[field] = source[field]


def _extract_name_from_json_ld_person(value):
    if isinstance(value, dict):
        return clean_text(value.get("name"))
    if isinstance(value, list):
        for item in value:
            name = _extract_name_from_json_ld_person(item)
            if name:
                return name
    return clean_text(value)


def _extract_name_from_json_ld_album(value):
    if isinstance(value, dict):
        return clean_text(value.get("name"))
    if isinstance(value, list):
        for item in value:
            name = _extract_name_from_json_ld_album(item)
            if name:
                return name
    return clean_text(value)


def _iter_json_ld_objects(payload):
    if isinstance(payload, dict):
        yield payload
        graph = payload.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    yield item
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item


def _json_ld_type_score(obj, entity_type):
    raw_type = obj.get("@type")
    if isinstance(raw_type, list):
        types = {str(item).lower() for item in raw_type}
    elif raw_type:
        types = {str(raw_type).lower()}
    else:
        types = set()

    ignored_types = {"breadcrumblist", "website", "organization", "person"}
    if types & ignored_types:
        return -1

    has_relevant_music_type = "musicrecording" in types or "musicalbum" in types
    if not has_relevant_music_type:
        return 0

    score = 0
    if entity_type == "track":
        if "musicrecording" in types:
            score += 100
        if "musicalbum" in types:
            score += 30
    elif entity_type == "album":
        if "musicalbum" in types:
            score += 100
        if "musicrecording" in types:
            score += 20

    if clean_text(obj.get("name")):
        score += 10
    if _extract_name_from_json_ld_person(obj.get("byArtist")):
        score += 10
    if _extract_name_from_json_ld_album(obj.get("inAlbum")):
        score += 5

    return score


def _extract_json_ld_metadata(obj, entity_type):
    result = {
        "title": clean_text(obj.get("name")),
        "artist": _extract_name_from_json_ld_person(obj.get("byArtist")),
        "album": None,
    }

    if entity_type == "track":
        result["album"] = _extract_name_from_json_ld_album(obj.get("inAlbum"))
    elif entity_type == "album":
        result["album"] = clean_text(obj.get("name"))

    return result


def _parse_title_like_value(raw_value):
    raw = clean_text(raw_value)
    if not raw:
        return {"title": None, "artist": None, "album": None}

    match = re.match(r"(.+?) by (.+?) on TIDAL", raw, flags=re.IGNORECASE)
    if match:
        return {
            "title": clean_text(match.group(1)),
            "artist": clean_text(match.group(2)),
            "album": None,
        }

    parts = raw.split(" - ")
    if len(parts) == 2:
        return {
            "title": clean_text(parts[1]),
            "artist": clean_text(parts[0]),
            "album": None,
        }

    return {"title": raw, "artist": None, "album": None}


def _extract_best_json_ld_metadata(soup, entity_type):
    candidates = []
    json_ld_blocks = soup.find_all("script", attrs={"type": "application/ld+json"})

    for block in json_ld_blocks:
        content = block.string or block.text
        if not content or not content.strip():
            continue

        try:
            payload = json.loads(content)
        except Exception:
            continue

        for obj in _iter_json_ld_objects(payload):
            score = _json_ld_type_score(obj, entity_type)
            if score <= 0:
                continue

            candidates.append((score, _extract_json_ld_metadata(obj, entity_type)))

    if not candidates:
        return {}

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]




def parse_tidal_metadata_from_html(html_text, entity_type):
    soup = BeautifulSoup(html_text, "lxml")

    result = {"title": None, "artist": None, "album": None}

    _fill_missing_fields(result, _extract_best_json_ld_metadata(soup, entity_type))

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        _fill_missing_fields(result, _parse_title_like_value(og_title.get("content")))

    twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
    if twitter_title and twitter_title.get("content"):
        _fill_missing_fields(result, _parse_title_like_value(twitter_title.get("content")))

    if soup.title and soup.title.string:
        _fill_missing_fields(result, _parse_title_like_value(soup.title.string))

    return result


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




def normalize_audio_genres(raw_genres):
    return normalize_audio_prediction_genres(raw_genres, min_prob=0.05)


def merge_final_genres(release_genres, audio_genres_pretty, entity_type):
    release_genres = [g for g in normalize_genres(release_genres) if is_allowed_final_genre(g)]
    audio_genres_pretty = [g for g in normalize_genres(audio_genres_pretty) if is_allowed_final_genre(g)]
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
        add("post rock")

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
    final_genres = [g for g in result.get("final_genres", []) if is_allowed_final_genre(g)]

    artist_tag = slugify_for_tag(artist)
    genre_tags = [genre_to_blog_tag(g) for g in final_genres if genre_to_blog_tag(g)]

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
    def _do():
        suffix = Path(filename or "audio.mp3").suffix.lower() or ".bin"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        try:
            with open(temp_path, "rb") as f:
                response = requests.post(
                    settings.get_audio_classifier_url(),
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
                Path(temp_path).unlink()
            except Exception:
                pass

    return run_timed_stage_sync("audio_classifier", _do)


async def compute_result(url):
    info = extract_tidal_id(url)
    tidal_data = await run_timed_stage("parse_tidal", parse_tidal(url))

    release_title = tidal_data.get("title") if info["type"] == "album" else (
        tidal_data.get("album") or tidal_data.get("title")
    )

    discogs_data = await run_timed_stage(
        "discogs",
        search_discogs_release_metadata(
            tidal_data.get("artist"),
            release_title,
        ),
    )

    async def _musicbrainz():
        mb_data = await search_musicbrainz_release_info(
            tidal_data.get("artist"),
            tidal_data.get("title"),
            tidal_data.get("album"),
            tidal_data.get("entity_type"),
        )
        artist_country_tag = None
        if mb_data.get("outcome") == "success" and mb_data.get("artist_id"):
            artist_country_tag = await search_artist_country_tag(
                tidal_data.get("artist"),
                mb_data.get("artist_id"),
            )
        else:
            artist_country_tag = await search_artist_country_tag(
                tidal_data.get("artist"),
            )
        return mb_data, artist_country_tag

    mb_data, artist_country_tag = await run_timed_stage("musicbrainz", _musicbrainz())
    mb_success = mb_data.get("outcome") == "success"

    release_year = discogs_data.get("release_year")
    if not release_year and mb_success and mb_data.get("release_year") and mb_data.get("confidence", 0) >= 0.65:
        release_year = mb_data.get("release_year")

    if tidal_data.get("entity_type") == "album":
        release_kind = "album"
        if mb_success and mb_data.get("release_kind") in ["album", "ep"]:
            release_kind = mb_data.get("release_kind")
    else:
        release_kind = "single"
        if mb_success and mb_data.get("release_kind") in ["single", "ep"] and mb_data.get("confidence", 0) >= 0.75:
            release_kind = mb_data.get("release_kind")

    result = {
        **tidal_data,
        "genres": discogs_data.get("genres", []),
        "meta_source_url": discogs_data.get("meta_source_url"),
        "source_name": discogs_data.get("source_name"),
        "note": discogs_data.get("note"),
        "release_year": release_year,
        "country": country_display_from_tag(artist_country_tag),
        "artist_country_tag": artist_country_tag,
        "release_kind": release_kind,
        "mb_release_date": mb_data.get("release_date"),
        "mb_confidence": mb_data.get("confidence"),
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "final_genres": normalize_genres(discogs_data.get("genres", [])),
        "audio_note": None,
        "from_cache": False,
    }

    result = _normalize_country_fields(result)
    result["blog_output"] = build_blog_output(result)
    return result


async def build_result(url, force_refresh=False, baseline=None):
    cache_key = build_cache_key(url)
    cached = get_cached_result(cache_key)
    if baseline is not None and not _is_valid_cached_payload(baseline):
        baseline = None

    if force_refresh:
        metrics.increment_force_refresh_total()

    if not force_refresh and cached:
        metrics.increment_cache_hit_total()
        logger.info(
            "event=cache_lookup outcome=hit source=cache cache_key=%s from_cache=true force_refresh=%s",
            cache_key,
            force_refresh,
        )
        return cached

    metrics.increment_cache_miss_total()
    logger.info(
        "event=cache_lookup outcome=miss source=cache cache_key=%s from_cache=false force_refresh=%s",
        cache_key,
        force_refresh,
    )

    previous = baseline or cached
    result = await compute_result(url)
    result = merge_prefer_better(previous, result)
    result = _normalize_country_fields(result)
    result["blog_output"] = build_blog_output(result)

    save_cached_result(result)
    if _is_degraded_result(result):
        metrics.increment_degraded_result_total()
    logger.info(
        "event=result_build outcome=success source=tidal_parser entity_type=%s from_cache=false force_refresh=%s final_genres_count=%d",
        result.get("entity_type"),
        force_refresh,
        len(result.get("final_genres", [])),
    )
    return result


@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": None, "error": None, "form_url": ""},
    )


@app.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def parse_form(
    request: Request,
    url: str = Form(...),
    force_refresh: str = Form(default="0"),
    audio: UploadFile = File(default=None),
):
    request_id = getattr(request.state, "request_id", None)
    metrics.increment_requests_total()
    try:
        url = validate_user_input_url(url)
        result = await build_result(url, force_refresh=(force_refresh == "1"))

        if audio and audio.filename:
            audio_bytes = await audio.read()
            if audio_bytes:
                audio_info = await asyncio.to_thread(
                    classify_audio_file,
                    audio_bytes,
                    audio.filename,
                )
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
        elif force_refresh == "1":
            result["audio_note"] = "Обновление без кэша не повторяет аудио-анализ. Если нужен новый audio-анализ, загрузи файл заново."

        metrics.increment_parse_success_total()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": result,
                "error": None,
                "error_request_id": None,
                "form_url": url,
            },
        )
    except ClientInputError as e:
        logger.warning(
            "event=parse_form outcome=client_error path=%s url=%s error=%s",
            request.url.path,
            url,
            str(e),
        )
        metrics.increment_parse_error_total()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": str(e),
                "error_request_id": request_id,
                "form_url": url,
            },
            status_code=400,
        )
    except Exception:
        logger.exception(
            "event=parse_form outcome=server_error path=%s url=%s",
            request.url.path,
            url,
        )
        metrics.increment_parse_error_total()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": "Не удалось обработать запрос. Попробуй ещё раз позже.",
                "error_request_id": request_id,
                "form_url": url,
            },
            status_code=500,
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
            {"request": request, "result": result, "error": None, "form_url": url},
        )
    except Exception as e:
        if old_cached:
            old_cached["audio_note"] = "Не удалось безопасно пересобрать кэш. Показан последний хороший результат."
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "result": old_cached, "error": str(e), "form_url": url},
                status_code=400,
            )

        return RedirectResponse(url="/", status_code=303)


@app.get("/api/parse")
@limiter.limit("10/minute")
async def parse_api(request: Request, url: str, force_refresh: int = 0):
    request_id = getattr(request.state, "request_id", None)
    metrics.increment_requests_total()
    try:
        url = validate_user_input_url(url)
        result = await build_result(url, force_refresh=(force_refresh == 1))
        metrics.increment_parse_success_total()
        return {"ok": True, "data": result}
    except ClientInputError as e:
        logger.warning(
            "event=parse_api outcome=client_error path=%s url=%s error=%s",
            request.url.path,
            url,
            str(e),
        )
        metrics.increment_parse_error_total()
        return JSONResponse(
            {"ok": False, "error": str(e), "request_id": request_id},
            status_code=400,
        )
    except Exception:
        logger.exception(
            "event=parse_api outcome=server_error path=%s url=%s",
            request.url.path,
            url,
        )
        metrics.increment_parse_error_total()
        return JSONResponse(
            {
                "ok": False,
                "error": "Внутренняя ошибка сервера. Попробуй позже.",
                "request_id": request_id,
            },
            status_code=500,
        )


@app.get("/metrics")
async def get_metrics():
    return metrics.snapshot_with_metadata()


@app.get("/health")
@limiter.limit("30/minute")
async def health(request: Request):
    return {"ok": True}
