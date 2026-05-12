import asyncio
import base64
import html
import logging
import os
import re
import time
from urllib.parse import quote_plus

import httpx


logger = logging.getLogger("tidal_parser")

TIDAL_API_BASE_URL = "https://openapi.tidal.com/v2"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_COUNTRY_CODE = "US"
TIDAL_CANDIDATE_LIMIT = 5
TIDAL_TOKEN_REFRESH_SKEW_S = 60

_TIDAL_TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0.0,
}
_TIDAL_TOKEN_LOCK = asyncio.Lock()


def clean_text(value):
    if value is None:
        return None

    text = html.unescape(str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def get_tidal_credentials():
    client_id = clean_text(os.getenv("TIDAL_CLIENT_ID"))
    client_secret = clean_text(os.getenv("TIDAL_CLIENT_SECRET"))
    return client_id, client_secret


def reset_tidal_openapi_state():
    _TIDAL_TOKEN_CACHE["access_token"] = None
    _TIDAL_TOKEN_CACHE["expires_at"] = 0.0


def build_tidal_candidate_url(resource_type, resource_id):
    resource_type = clean_text(resource_type)
    resource_id = clean_text(resource_id)
    if not resource_type or not resource_id:
        return None

    if resource_type in {"album", "albums"}:
        slug = "album"
    elif resource_type in {"track", "tracks"}:
        slug = "track"
    else:
        return None

    return "https://tidal.com/{}/{}".format(slug, quote_plus(resource_id))


def build_tidal_openapi_search_query(artist, title):
    artist = clean_text(artist)
    title = _normalize_tidal_search_title(title)
    if not artist or not title:
        return None

    return "{} {}".format(artist, title)


def _normalize_tidal_search_title(title):
    title = clean_text(title)
    if not title:
        return None

    title = title.strip(' "\'“”‘’`')
    title = re.sub(r"[!?.,…]+$", "", title).strip()
    title = title.strip(' "\'“”‘’`')
    title = re.sub(r"\s+", " ", title).strip()
    return title or None


def _normalize_release_type(release_type):
    release_type = clean_text(release_type)
    if not release_type:
        return None
    return release_type.lower()


def _relation_for_release_type(release_type):
    release_type = _normalize_release_type(release_type)
    if release_type in {"album", "ep", "lp"}:
        return ["albums"]
    if release_type in {"single", "track"}:
        return ["tracks"]
    return ["albums", "tracks"]


def _candidate_type_from_relation(relation):
    if relation == "albums":
        return "album"
    if relation == "tracks":
        return "track"
    return clean_text(relation)


def _resource_key(resource):
    if not isinstance(resource, dict):
        return None
    resource_id = clean_text(resource.get("id"))
    resource_type = clean_text(resource.get("type"))
    if not resource_id or not resource_type:
        return None
    return (resource_type, resource_id)


def _candidate_from_resource(resource, relation, query_artist, query_title):
    if not isinstance(resource, dict):
        return None

    attrs = resource.get("attributes")
    if not isinstance(attrs, dict):
        attrs = {}

    candidate_type = _candidate_type_from_relation(relation)
    candidate_id = clean_text(resource.get("id"))
    candidate_title = clean_text(attrs.get("title") or attrs.get("name") or resource.get("title") or resource.get("name"))
    release_date = clean_text(attrs.get("releaseDate") or attrs.get("release_date") or resource.get("releaseDate"))
    year = release_date[:4] if release_date and re.match(r"^\d{4}[-/]", release_date) else None
    tidal_url = build_tidal_candidate_url(candidate_type, candidate_id)

    display_parts = [candidate_title or "—"]
    if release_date:
        display_parts.append("({})".format(release_date if len(release_date) > 4 else release_date))
    elif year:
        display_parts.append("({})".format(year))
    if candidate_type:
        display_parts.append("[{}]".format(candidate_type))

    candidate = {
        "id": candidate_id,
        "type": candidate_type,
        "title": candidate_title,
        "release_date": release_date,
        "year": year,
        "tidal_url": tidal_url,
        "display_line": " ".join(display_parts),
        "query_artist": clean_text(query_artist),
        "query_title": clean_text(query_title),
    }
    return candidate


def _parse_candidates_from_payload(payload, relation, query_artist, query_title, limit):
    if not isinstance(payload, dict) or limit <= 0:
        return []

    included_map = {}
    included = payload.get("included")
    if isinstance(included, list):
        for item in included:
            key = _resource_key(item)
            if key:
                included_map[key] = item

    resources = []
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            key = _resource_key(item)
            resources.append(included_map.get(key, item))
    elif isinstance(data, dict):
        key = _resource_key(data)
        resources.append(included_map.get(key, data))

    candidates = []
    seen_ids = set()
    for resource in resources:
        candidate = _candidate_from_resource(resource, relation, query_artist, query_title)
        if not candidate or not candidate.get("id"):
            continue
        candidate_key = (candidate.get("type"), candidate.get("id"))
        if candidate_key in seen_ids:
            continue
        seen_ids.add(candidate_key)
        candidates.append(candidate)
        if len(candidates) >= limit:
            break

    return candidates


async def _request_json(method, url, headers=None, data=None, params=None):
    request_headers = headers or {}
    async with httpx.AsyncClient(timeout=20, headers=request_headers) as client:
        response = await client.request(
            method,
            url,
            data=data,
            params=params,
            follow_redirects=True,
        )

    content_type = response.headers.get("content-type", "")
    text = response.text or ""
    payload = None
    if "json" in content_type.lower() or text.lstrip().startswith("{") or text.lstrip().startswith("["):
        try:
            payload = response.json()
        except Exception:
            payload = None

    return {
        "status": response.status_code,
        "content_type": content_type,
        "text": text,
        "json": payload,
    }


async def _request_access_token(client_id, client_secret):
    basic = base64.b64encode("{}:{}".format(client_id, client_secret).encode("utf-8")).decode("ascii")
    result = await _request_json(
        "POST",
        TIDAL_TOKEN_URL,
        headers={
            "Authorization": "Basic {}".format(basic),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={"grant_type": "client_credentials"},
    )
    token_payload = result.get("json") if isinstance(result, dict) else None
    if not isinstance(token_payload, dict):
        return None, result

    access_token = clean_text(token_payload.get("access_token"))
    if not access_token:
        return None, result

    expires_in = token_payload.get("expires_in") or 0
    try:
        expires_in = int(expires_in)
    except (TypeError, ValueError):
        expires_in = 0
    if expires_in < 0:
        expires_in = 0

    _TIDAL_TOKEN_CACHE["access_token"] = access_token
    _TIDAL_TOKEN_CACHE["expires_at"] = time.time() + max(expires_in - TIDAL_TOKEN_REFRESH_SKEW_S, 0)

    return access_token, result


async def _get_access_token():
    client_id, client_secret = get_tidal_credentials()
    if not client_id or not client_secret:
        return None

    now = time.time()
    cached_token = _TIDAL_TOKEN_CACHE.get("access_token")
    expires_at = float(_TIDAL_TOKEN_CACHE.get("expires_at") or 0)
    if cached_token and now < expires_at:
        return cached_token

    async with _TIDAL_TOKEN_LOCK:
        cached_token = _TIDAL_TOKEN_CACHE.get("access_token")
        expires_at = float(_TIDAL_TOKEN_CACHE.get("expires_at") or 0)
        if cached_token and now < expires_at:
            return cached_token

        access_token, token_result = await _request_access_token(client_id, client_secret)
        if access_token:
            return access_token

        status = token_result.get("status") if isinstance(token_result, dict) else None
        logger.warning(
            "event=tidal_openapi_token outcome=error status=%s",
            status,
        )
        return None


async def _fetch_relationship_payload(query, relation, access_token, country_code=TIDAL_COUNTRY_CODE):
    query = clean_text(query)
    relation = clean_text(relation)
    if not query or relation not in {"albums", "tracks"}:
        return {
            "state": "error",
            "message": "Не удалось получить кандидатов TIDAL. Используй ручной поиск.",
            "payload": None,
        }

    url = "{}/searchResults/{}/relationships/{}".format(
        TIDAL_API_BASE_URL,
        quote_plus(query),
        relation,
    )

    result = await _request_json(
        "GET",
        url,
        headers={
            "Authorization": "Bearer {}".format(access_token),
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        params={
            "countryCode": country_code,
            "include": relation,
            "explicitFilter": "INCLUDE",
        },
    )

    return {
        "state": "ok" if result.get("status") == 200 else "error",
        "message": None if result.get("status") == 200 else "Не удалось получить кандидатов TIDAL. Используй ручной поиск.",
        "payload": result.get("json"),
        "status": result.get("status"),
        "content_type": result.get("content_type"),
    }


async def lookup_tidal_candidates(artist, title, release_type=None, year=None, country_code=TIDAL_COUNTRY_CODE):
    query = build_tidal_openapi_search_query(artist, title)
    if not query:
        return {
            "state": "disabled",
            "message": None,
            "query": None,
            "release_type": clean_text(release_type),
            "candidates": [],
        }

    client_id, client_secret = get_tidal_credentials()
    if not client_id or not client_secret:
        return {
            "state": "disabled",
            "message": "TIDAL Open API credentials are not configured. Используй ручной поиск в TIDAL.",
            "query": query,
            "release_type": clean_text(release_type),
            "candidates": [],
        }

    access_token = await _get_access_token()
    if not access_token:
        return {
            "state": "error",
            "message": "Не удалось получить кандидатов TIDAL. Используй ручной поиск.",
            "query": query,
            "release_type": clean_text(release_type),
            "candidates": [],
        }

    relations = _relation_for_release_type(release_type)
    candidates = []
    last_error_message = None

    for relation in relations:
        remaining = TIDAL_CANDIDATE_LIMIT - len(candidates)
        if remaining <= 0:
            break

        fetched = await _fetch_relationship_payload(query, relation, access_token, country_code=country_code)
        payload = fetched.get("payload")
        if fetched.get("state") == "error":
            last_error_message = fetched.get("message") or last_error_message
            continue

        relation_candidates = _parse_candidates_from_payload(payload, relation, artist, title, remaining)
        candidates.extend(relation_candidates)
        if len(candidates) >= TIDAL_CANDIDATE_LIMIT:
            break

    if candidates:
        return {
            "state": "success",
            "message": None,
            "query": query,
            "release_type": clean_text(release_type),
            "candidates": candidates[:TIDAL_CANDIDATE_LIMIT],
        }

    if last_error_message:
        return {
            "state": "error",
            "message": last_error_message,
            "query": query,
            "release_type": clean_text(release_type),
            "candidates": [],
        }

    return {
        "state": "empty",
        "message": "Кандидаты TIDAL не найдены. Используй ручной поиск в TIDAL.",
        "query": query,
        "release_type": clean_text(release_type),
        "candidates": [],
    }
