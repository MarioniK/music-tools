"""Извлечение Yandex Music identity и TIDAL bridge через Odesli/Songlink."""

from __future__ import annotations

import json
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse, urlunparse
from urllib.request import Request, urlopen


MAX_ODESLI_JSON_BYTES = 1024 * 1024
ODESLI_FETCH_TIMEOUT_SECONDS = 8
ODESLI_USER_AGENT = "music-tools/1.0 (+https://github.com/MarioniK/music-tools)"

_ALLOWED_YANDEX_HOSTS = {"music.yandex.ru", "music.yandex.com"}


def _clean_text(value):
    if value is None:
        return None
    text = unescape(str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def _normalize_host(netloc: str) -> str:
    host = (netloc or "").lower().strip()
    if ":" in host:
        host = host.split(":", 1)[0]
    return host


def _is_allowed_yandex_music_host(host: str) -> bool:
    if not host:
        return False
    if host in _ALLOWED_YANDEX_HOSTS:
        return True
    return host.endswith(".yandex.ru") or host.endswith(".yandex.com")


def is_supported_yandex_music_url(url: str) -> bool:
    """Проверяет, относится ли URL к поддерживаемому Yandex Music релизу."""

    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    if not _is_allowed_yandex_music_host(_normalize_host(parsed.netloc)):
        return False

    return bool(extract_yandex_ids_from_url(url))


def extract_yandex_ids_from_url(url: str):
    """Возвращает album_id / track_id для Yandex Music album или track URL."""

    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {}

    if not _is_allowed_yandex_music_host(_normalize_host(parsed.netloc)):
        return {}

    path = parsed.path or ""
    match = re.search(r"^/album/(\d+)(?:/track/(\d+))?(?:/|$)", path)
    if not match:
        return {}

    album_id = match.group(1)
    track_id = match.group(2)
    release_type = "track" if track_id else "album"

    return {
        "yandex_album_id": album_id,
        "yandex_track_id": track_id,
        "provider_item_id": track_id or album_id,
        "release_type": release_type,
    }


def normalize_tidal_url(url: str):
    """Нормализует listen.tidal.com URL в canonical tidal.com URL."""

    cleaned = _clean_text(url)
    if not cleaned:
        return None

    parsed = urlparse(cleaned)
    host = _normalize_host(parsed.netloc)
    if host not in {"tidal.com", "www.tidal.com", "listen.tidal.com"} and not host.endswith(".tidal.com"):
        return cleaned

    path = parsed.path or ""
    if not path:
        return cleaned

    normalized = urlunparse(("https", "tidal.com", path, "", "", ""))
    return normalized


def extract_tidal_url_from_odesli(odesli_payload):
    """Возвращает TIDAL URL из payload Odesli, если он присутствует."""

    if not isinstance(odesli_payload, dict):
        return None

    links_by_platform = odesli_payload.get("linksByPlatform")
    if not isinstance(links_by_platform, dict):
        return None

    tidal_link = links_by_platform.get("tidal")
    if not isinstance(tidal_link, dict):
        return None

    return normalize_tidal_url(tidal_link.get("url"))


def fetch_odesli_links(url: str, user_country: str | None = None):
    """Загружает public Odesli JSON для provider URL."""

    normalized_url = _clean_text(url)
    if not normalized_url:
        return {
            "ok": False,
            "status": None,
            "api_url": None,
            "payload": None,
            "warnings": ["Пустой URL для Odesli."],
            "error": "Пустой URL для Odesli.",
        }

    api_url = "https://api.song.link/v1-alpha.1/links?url={}".format(quote(normalized_url, safe=""))
    if user_country:
        api_url += "&userCountry={}".format(user_country)

    request = Request(
        api_url,
        headers={
            "Accept": "application/json",
            "User-Agent": ODESLI_USER_AGENT,
        },
    )

    warnings = []
    try:
        with urlopen(request, timeout=ODESLI_FETCH_TIMEOUT_SECONDS) as response:
            status = response.getcode()
            raw_payload = response.read(MAX_ODESLI_JSON_BYTES + 1)
            if len(raw_payload) > MAX_ODESLI_JSON_BYTES:
                raw_payload = raw_payload[:MAX_ODESLI_JSON_BYTES]
                warnings.append("Odesli JSON был обрезан до 1 MB.")

            text = raw_payload.decode("utf-8", errors="replace")
            try:
                payload = json.loads(text) if text else None
            except Exception:
                payload = None

            ok = status == 200 and isinstance(payload, dict)
            if not ok:
                warnings.append("Odesli ответил некорректным JSON.")

            return {
                "ok": ok,
                "status": status,
                "api_url": api_url,
                "payload": payload if isinstance(payload, dict) else None,
                "warnings": warnings,
                "error": None if ok else "Odesli response was not usable.",
            }
    except HTTPError as exc:
        body = b""
        if exc.fp is not None:
            try:
                body = exc.fp.read(MAX_ODESLI_JSON_BYTES + 1)
            except Exception:
                body = b""

        if len(body) > MAX_ODESLI_JSON_BYTES:
            body = body[:MAX_ODESLI_JSON_BYTES]
            warnings.append("Odesli JSON был обрезан до 1 MB.")

        payload = None
        if body:
            try:
                payload = json.loads(body.decode("utf-8", errors="replace"))
            except Exception:
                payload = None

        if payload is None:
            warnings.append("Odesli request returned HTTP {}.".format(getattr(exc, "code", "error")))

        return {
            "ok": False,
            "status": getattr(exc, "code", None),
            "api_url": api_url,
            "payload": payload if isinstance(payload, dict) else None,
            "warnings": warnings,
            "error": "Odesli request failed with HTTP {}.".format(getattr(exc, "code", "error")),
        }
    except URLError:
        warnings.append("Не удалось загрузить Odesli ответ.")
        return {
            "ok": False,
            "status": None,
            "api_url": api_url,
            "payload": None,
            "warnings": warnings,
            "error": "Не удалось загрузить Odesli ответ.",
        }


def _extract_odesli_entity(payload):
    if not isinstance(payload, dict):
        return {}

    entities = payload.get("entitiesByUniqueId")
    if not isinstance(entities, dict):
        return {}

    entity_unique_id = payload.get("entityUniqueId")
    if entity_unique_id and isinstance(entities.get(entity_unique_id), dict):
        return entities.get(entity_unique_id) or {}

    for entity in entities.values():
        if isinstance(entity, dict):
            return entity

    return {}


def _map_odesli_type(release_type, yandex_ids):
    release_type = _clean_text(release_type)
    if release_type == "album":
        return "album"
    if release_type == "song":
        return "track"
    if isinstance(yandex_ids, dict) and yandex_ids.get("release_type") in {"album", "track"}:
        return yandex_ids.get("release_type")
    return None


def extract_odesli_yandex_identity(source_url: str, odesli_result: dict | None = None):
    """Возвращает нормализованную identity Yandex Music через Odesli."""

    normalized_source_url = _clean_text(source_url)
    yandex_ids = extract_yandex_ids_from_url(normalized_source_url)

    if not normalized_source_url:
        return {
            "input_state": "extracted_release_identity",
            "provider": "yandex_music",
            "provider_label": "Yandex Music",
            "source_url": source_url,
            "original_url": source_url,
            "resolved_metadata_url": None,
            "canonical_url": None,
            "odesli_page_url": None,
            "odesli_tidal_url": None,
            "provider_item_id": None,
            "yandex_album_id": None,
            "yandex_track_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": ["Пустой URL Yandex Music."],
        }

    if not yandex_ids:
        return {
            "input_state": "extracted_release_identity",
            "provider": "yandex_music",
            "provider_label": "Yandex Music",
            "source_url": normalized_source_url,
            "original_url": normalized_source_url,
            "resolved_metadata_url": None,
            "canonical_url": None,
            "odesli_page_url": None,
            "odesli_tidal_url": None,
            "provider_item_id": None,
            "yandex_album_id": None,
            "yandex_track_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": [
                "Поддерживаются только Yandex Music album/track ссылки.",
            ],
        }

    if odesli_result is None:
        odesli_result = fetch_odesli_links(normalized_source_url)

    warnings = list(odesli_result.get("warnings") or []) if isinstance(odesli_result, dict) else []
    payload = odesli_result.get("payload") if isinstance(odesli_result, dict) else None
    entity = _extract_odesli_entity(payload)

    title = _clean_text(entity.get("title"))
    artist = _clean_text(entity.get("artistName"))
    release_type = _map_odesli_type(entity.get("type"), yandex_ids)
    odesli_page_url = _clean_text(payload.get("pageUrl")) if isinstance(payload, dict) else None
    tidal_url = extract_tidal_url_from_odesli(payload)
    canonical_url = urlunparse(urlparse(normalized_source_url)._replace(query="", fragment=""))
    cover_url = _clean_text(entity.get("thumbnailUrl"))

    if not title and not artist:
        warnings.append("Yandex Music metadata не удалось получить через Odesli.")

    if not tidal_url and release_type == "album":
        warnings.append("Odesli не вернул TIDAL URL для этого Yandex Music album.")

    if not tidal_url and release_type == "track":
        warnings.append("Odesli не вернул TIDAL URL для этого Yandex Music track.")

    confidence = "low"
    if title and artist and release_type:
        confidence = "high" if tidal_url else "medium"
    elif title or artist:
        confidence = "medium"

    return {
        "input_state": "extracted_release_identity",
        "provider": "yandex_music",
        "provider_label": "Yandex Music",
        "source_url": normalized_source_url,
        "original_url": normalized_source_url,
        "resolved_metadata_url": odesli_page_url,
        "canonical_url": canonical_url,
        "odesli_page_url": odesli_page_url,
        "odesli_tidal_url": tidal_url,
        "provider_item_id": yandex_ids.get("provider_item_id"),
        "yandex_album_id": yandex_ids.get("yandex_album_id"),
        "yandex_track_id": yandex_ids.get("yandex_track_id"),
        "artist": artist,
        "title": title,
        "year": None,
        "release_date": None,
        "release_type": release_type,
        "cover_url": cover_url,
        "api_provider": _clean_text(entity.get("apiProvider")) if isinstance(entity, dict) else None,
        "entity_unique_id": _clean_text(payload.get("entityUniqueId")) if isinstance(payload, dict) else None,
        "extraction_method": "odesli",
        "primary_source": "odesli",
        "confidence": confidence,
        "warnings": warnings,
    }
