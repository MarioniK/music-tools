"""Извлечение минимальной identity релиза из Qobuz HTML-страницы."""

from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_QOBUZ_HTML_BYTES = 1024 * 1024
QOBUZ_FETCH_TIMEOUT_SECONDS = 5
QOBUZ_USER_AGENT = "music-tools/1.0 (+https://github.com/MarioniK/music-tools)"

_ALLOWED_QOBUZ_HOSTS = {"qobuz.com", "www.qobuz.com", "play.qobuz.com", "open.qobuz.com"}
_GENERIC_QOBUZ_TITLES = {
    "open qobuz",
    "qobuz",
    "listen on qobuz",
    "qobuz - open",
    "open - qobuz",
}
_GENERIC_QOBUZ_ARTISTS = _GENERIC_QOBUZ_TITLES | {
    "music",
    "album",
    "track",
    "single",
    "ep",
    "release",
}


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


def _is_allowed_qobuz_host(host: str) -> bool:
    if not host:
        return False

    if host in _ALLOWED_QOBUZ_HOSTS:
        return True

    return host.endswith(".qobuz.com")


def _is_allowed_qobuz_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    return _is_allowed_qobuz_host(_normalize_host(parsed.netloc))


def extract_open_qobuz_album_id(url: str):
    """Возвращает token альбома из open.qobuz.com deep-link, если он безопасно распознан."""

    parsed = urlparse((url or "").strip())
    if _normalize_host(parsed.netloc) != "open.qobuz.com":
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or parts[0] != "album":
        return None

    album_id = _clean_text(parts[1])
    return album_id or None


class _QobuzRedirectHandler(HTTPRedirectHandler):
    """Ограничивает редиректы только Qobuz-хостами."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme not in {"http", "https"}:
            return None

        if not _is_allowed_qobuz_host(_normalize_host(parsed.netloc)):
            return None

        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _QobuzHTMLMetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_text = ""
        self._in_title = False
        self._in_json_ld = False
        self._json_ld_buffer = []
        self.meta = {}
        self.json_ld_blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = {key.lower(): value for key, value in attrs}

        if tag == "title":
            self._in_title = True
            return

        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            content = attrs.get("content")
            if key and content:
                self.meta[key.lower()] = content.strip()
            return

        if tag == "script" and (attrs.get("type") or "").lower() == "application/ld+json":
            self._in_json_ld = True
            self._json_ld_buffer = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            return

        if tag == "script" and self._in_json_ld:
            content = "".join(self._json_ld_buffer).strip()
            if content:
                self.json_ld_blocks.append(content)
            self._in_json_ld = False
            self._json_ld_buffer = []

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data
        elif self._in_json_ld:
            self._json_ld_buffer.append(data)


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


def _extract_name(value):
    if isinstance(value, dict):
        return _clean_text(value.get("name"))

    if isinstance(value, list):
        for item in value:
            name = _extract_name(item)
            if name:
                return name

    return _clean_text(value)


def _is_generic_qobuz_artist(value):
    cleaned = _strip_qobuz_suffix(value)
    if not cleaned:
        return True

    normalized = re.sub(r"\s+", " ", cleaned).strip().lower()
    if normalized in _GENERIC_QOBUZ_ARTISTS:
        return True

    if re.fullmatch(r"(?:qobuz|open qobuz|listen on qobuz|music|album|track|single|ep|release)", normalized):
        return True

    return False


def _extract_qobuz_artist_name(value):
    if isinstance(value, dict):
        nested_name = value.get("name")
        if isinstance(nested_name, (dict, list)):
            artist = _extract_qobuz_artist_name(nested_name)
            if artist:
                return artist
        else:
            direct_name = _clean_text(nested_name)
            if direct_name and not _is_generic_qobuz_artist(direct_name):
                return direct_name

        for key in ("byArtist", "artist", "creator", "performer", "member", "@graph", "@list"):
            artist = _extract_qobuz_artist_name(value.get(key))
            if artist:
                return artist

        return None

    if isinstance(value, list):
        for item in value:
            artist = _extract_qobuz_artist_name(item)
            if artist:
                return artist
        return None

    text = _clean_text(value)
    if text and not _is_generic_qobuz_artist(text):
        return text

    return None


def _extract_cover_url(value):
    if isinstance(value, dict):
        return _clean_text(value.get("url") or value.get("contentUrl") or value.get("image"))

    if isinstance(value, list):
        for item in value:
            cover_url = _extract_cover_url(item)
            if cover_url:
                return cover_url

    return _clean_text(value)


def _extract_date(value):
    if isinstance(value, dict):
        for key in ("datePublished", "dateCreated", "releaseDate", "uploadDate", "dateModified"):
            candidate = _clean_text(value.get(key))
            if candidate:
                return candidate

    if isinstance(value, list):
        for item in value:
            candidate = _extract_date(item)
            if candidate:
                return candidate

    return _clean_text(value)


def _json_ld_release_type(types: Iterable[str]):
    type_set = {item.lower() for item in types if item}
    if "musicalbum" in type_set:
        return "album"
    if "musicrecording" in type_set:
        return "track"
    if "musicplaylist" in type_set:
        return "playlist"
    return None


def _parse_json_ld_candidate(obj):
    raw_type = obj.get("@type")
    if isinstance(raw_type, list):
        types = [str(item) for item in raw_type]
    elif raw_type:
        types = [str(raw_type)]
    else:
        types = []

    release_type = _json_ld_release_type(types)
    if not release_type:
        return None, 0

    candidate = {
        "artist": _extract_qobuz_artist_name(obj.get("byArtist") or obj.get("artist") or obj.get("creator")),
        "title": _clean_text(obj.get("name")),
        "year": None,
        "release_date": _extract_date(obj),
        "release_type": release_type,
        "cover_url": _extract_cover_url(obj.get("image") or obj.get("thumbnailUrl")),
    }

    if candidate["release_date"] and re.match(r"^\d{4}", candidate["release_date"]):
        candidate["year"] = int(candidate["release_date"][:4])

    score = 0
    if candidate["title"]:
        score += 10
    if candidate["artist"]:
        score += 10
    if candidate["release_date"]:
        score += 5
    if candidate["cover_url"]:
        score += 3

    if release_type in {"album", "track"}:
        score += 5

    return candidate, score


def _build_json_ld_identity(blocks):
    best_candidate = None
    best_score = -1

    for block in blocks:
        try:
            payload = json.loads(block)
        except Exception:
            continue

        for obj in _iter_json_ld_objects(payload):
            candidate, score = _parse_json_ld_candidate(obj)
            if candidate and score > best_score:
                best_candidate = candidate
                best_score = score

    if not best_candidate:
        return None

    best_candidate["extraction_method"] = "json_ld"
    best_candidate["primary_source"] = "json_ld"
    return best_candidate


def _strip_qobuz_suffix(value):
    cleaned = _clean_text(value)
    if not cleaned:
        return None

    cleaned = re.sub(r"\s*[\|\-–—]\s*Qobuz\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip() or None


def _is_generic_qobuz_title(value):
    cleaned = _strip_qobuz_suffix(value)
    if not cleaned:
        return False

    normalized = re.sub(r"\s+", " ", cleaned).strip().lower()
    if normalized in _GENERIC_QOBUZ_TITLES:
        return True

    if re.fullmatch(r"(?:qobuz|open|listen|music)(?:\s+on)?(?:\s+qobuz)?", normalized):
        return True

    return False


def _split_title_artist(value):
    cleaned = _strip_qobuz_suffix(value)
    if not cleaned:
        return None, None

    patterns = [
        r"^(?P<artist>.+?)\s*[–—-]\s*(?P<title>.+)$",
        r"^(?P<title>.+?)\s+by\s+(?P<artist>.+)$",
        r"^(?P<artist>.+?)\s*:\s*(?P<title>.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            artist = _clean_text(match.group("artist"))
            title = _clean_text(match.group("title"))
            if artist and title:
                return artist, title

    return None, cleaned


def _extract_artist_from_qobuz_title_source(title_source, known_title=None):
    cleaned = _strip_qobuz_suffix(title_source)
    if not cleaned or _is_generic_qobuz_title(cleaned):
        return None

    normalized_cleaned = re.sub(r"\s+", " ", cleaned).strip()
    normalized_title = _clean_text(known_title)
    if normalized_title:
        normalized_title = re.sub(r"\s+", " ", normalized_title).strip()
        lowered_cleaned = normalized_cleaned.lower()
        lowered_title = normalized_title.lower()

        if lowered_cleaned.startswith(lowered_title):
            remainder = normalized_cleaned[len(normalized_title) :].strip()
            if remainder.startswith(","):
                remainder = remainder[1:].strip()
            remainder = re.sub(r"^[\-\–—:\|]+", "", remainder).strip()
            if remainder and not _is_generic_qobuz_artist(remainder):
                return remainder

        if lowered_cleaned.startswith(lowered_title + ","):
            remainder = normalized_cleaned[len(normalized_title) + 1 :].strip()
            remainder = re.sub(r"^[\-\–—:\|]+", "", remainder).strip()
            if remainder and not _is_generic_qobuz_artist(remainder):
                return remainder

    if normalized_title and normalized_cleaned.count(",") == 1:
        left, right = [part.strip() for part in normalized_cleaned.split(",", 1)]
        if left.lower() == normalized_title.lower():
            right = re.sub(r"^[\-\–—:\|]+", "", right).strip()
            if right and not _is_generic_qobuz_artist(right):
                return right

    return None


def _extract_qobuz_artist_fallback(meta, title_source, known_title=None):
    for key in (
        "music:musician",
        "music:musicians",
        "music:artist",
        "artist",
        "author",
        "article:author",
        "dc.creator",
        "creator",
        "twitter:creator",
    ):
        artist = _clean_text(meta.get(key))
        if artist and not _is_generic_qobuz_artist(artist):
            return artist

    return _extract_artist_from_qobuz_title_source(title_source, known_title)


def _build_open_graph_identity(meta):
    title_source = meta.get("og:title") or meta.get("twitter:title")
    if not title_source:
        return None

    artist, title = _split_title_artist(title_source)
    if not title and not artist:
        return None

    release_date = (
        _clean_text(meta.get("music:release_date"))
        or _clean_text(meta.get("article:published_time"))
        or _clean_text(meta.get("article:modified_time"))
    )
    release_type_source = _clean_text(meta.get("og:type")) or ""
    if "album" in release_type_source.lower():
        release_type = "album"
    elif "song" in release_type_source.lower() or "track" in release_type_source.lower():
        release_type = "track"
    else:
        release_type = None

    year = None
    if release_date and re.match(r"^\d{4}", release_date):
        year = int(release_date[:4])

    cover_url = _clean_text(meta.get("og:image") or meta.get("twitter:image"))
    candidate = {
        "artist": artist,
        "title": title or artist,
        "year": year,
        "release_date": release_date,
        "release_type": release_type,
        "cover_url": cover_url,
        "extraction_method": "open_graph" if meta.get("og:title") else "twitter_card",
        "primary_source": "open_graph" if meta.get("og:title") else "twitter_card",
    }
    return candidate


def _build_html_title_identity(title_text):
    cleaned = _strip_qobuz_suffix(title_text)
    if not cleaned:
        return None

    if _is_generic_qobuz_title(cleaned):
        return None

    artist, title = _split_title_artist(cleaned)
    candidate = {
        "artist": artist,
        "title": title,
        "year": None,
        "release_date": None,
        "release_type": None,
        "cover_url": None,
        "extraction_method": "html_title",
        "primary_source": "html_title",
    }

    if not candidate["artist"] and not candidate["title"]:
        return None

    return candidate


def _finalize_identity(candidate, source_url, warnings, method_sources):
    if not candidate:
        return {
            "input_state": "extracted_release_identity",
            "provider": "qobuz",
            "source_url": source_url,
            "resolved_metadata_url": None,
            "qobuz_album_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "confidence": "low",
            "warnings": warnings or ["Не удалось извлечь metadata Qobuz."],
        }

    candidate = dict(candidate)
    candidate.setdefault("artist", None)
    candidate.setdefault("title", None)
    candidate.setdefault("year", None)
    candidate.setdefault("release_date", None)
    candidate.setdefault("release_type", None)
    candidate.setdefault("cover_url", None)
    candidate.setdefault("resolved_metadata_url", None)
    candidate.setdefault("qobuz_album_id", None)

    if candidate.get("year") is None and candidate.get("release_date") and re.match(r"^\d{4}", candidate["release_date"]):
        candidate["year"] = int(candidate["release_date"][:4])

    if candidate.get("artist") and candidate.get("title"):
        if candidate.get("primary_source") == "json_ld":
            confidence = "high"
        elif len(method_sources) > 1:
            confidence = "medium"
        else:
            confidence = "medium" if candidate.get("release_date") or candidate.get("cover_url") else "low"
    elif candidate.get("title"):
        confidence = "medium" if candidate.get("cover_url") else "low"
        if not candidate.get("artist"):
            warnings = list(warnings)
            warnings.append("Artist was not extracted from the Qobuz page.")
    else:
        confidence = "low"

    if not candidate.get("artist") and not candidate.get("title"):
        warnings = list(warnings)
        warnings.append("Qobuz page metadata found, but artist/title were not identified.")

    return {
        "input_state": "extracted_release_identity",
        "provider": "qobuz",
        "source_url": source_url,
        "resolved_metadata_url": candidate.get("resolved_metadata_url"),
        "qobuz_album_id": candidate.get("qobuz_album_id"),
        "artist": candidate.get("artist"),
        "title": candidate.get("title"),
        "year": candidate.get("year"),
        "release_date": candidate.get("release_date"),
        "release_type": candidate.get("release_type"),
        "cover_url": candidate.get("cover_url"),
        "extraction_method": candidate.get("extraction_method", "mixed"),
        "primary_source": candidate.get("primary_source"),
        "confidence": confidence,
        "warnings": warnings,
    }


def _identity_has_release_fields(identity):
    return bool(identity and identity.get("artist") and identity.get("title"))


def _build_open_qobuz_candidate_urls(album_id):
    return [
        "https://play.qobuz.com/album/{}".format(album_id),
        "https://www.qobuz.com/album/{}".format(album_id),
    ]


def _fetch_qobuz_html(url):
    request = Request(
        url,
        headers={
            "User-Agent": QOBUZ_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    opener = build_opener(_QobuzRedirectHandler())

    with opener.open(request, timeout=QOBUZ_FETCH_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("Content-Type", "")
        raw_bytes = response.read(MAX_QOBUZ_HTML_BYTES + 1)
        truncated = len(raw_bytes) > MAX_QOBUZ_HTML_BYTES
        html_text = raw_bytes[:MAX_QOBUZ_HTML_BYTES].decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        return html_text, content_type, truncated


def _extract_qobuz_identity_from_url(url):
    warnings = []

    try:
        html_text, content_type, truncated = _fetch_qobuz_html(url)
    except HTTPError as exc:
        warnings.append("Не удалось загрузить Qobuz страницу: HTTP {}.".format(getattr(exc, "code", "error")))
        return _finalize_identity(None, url, warnings, set())
    except URLError:
        warnings.append("Не удалось загрузить Qobuz страницу.")
        return _finalize_identity(None, url, warnings, set())
    except Exception:
        warnings.append("Не удалось загрузить Qobuz страницу.")
        return _finalize_identity(None, url, warnings, set())

    content_type = (content_type or "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        warnings.append("Qobuz response does not look like HTML.")

    if truncated:
        warnings.append("Qobuz HTML was truncated to 1 MB.")

    identity = parse_qobuz_release_identity_from_html(html_text, url)
    if warnings:
        identity["warnings"] = warnings + identity.get("warnings", [])

    return identity


def parse_qobuz_release_identity_from_html(html_text, source_url):
    parser = _QobuzHTMLMetadataParser()
    parser.feed(html_text or "")
    parser.close()

    warnings = []
    method_sources = set()

    json_ld_identity = _build_json_ld_identity(parser.json_ld_blocks)
    if json_ld_identity:
        method_sources.add("json_ld")

    og_identity = _build_open_graph_identity(parser.meta)
    if og_identity:
        method_sources.add(og_identity["extraction_method"])

    title_identity = _build_html_title_identity(parser.title_text)
    if title_identity:
        method_sources.add("html_title")
    elif _is_generic_qobuz_title(parser.title_text):
        warnings.append("Qobuz page returned generic metadata; release identity was not extracted.")

    candidate = json_ld_identity or og_identity or title_identity
    if candidate and json_ld_identity and (og_identity or title_identity):
        # JSON-LD считается основным источником, но дополнительные поля могут дополняться мета-тегами.
        candidate = dict(json_ld_identity)
        for field in ("artist", "title", "year", "release_date", "release_type", "cover_url"):
            if not candidate.get(field):
                source_candidate = og_identity or title_identity or {}
                if source_candidate.get(field):
                    candidate[field] = source_candidate.get(field)
        candidate["extraction_method"] = "json_ld" if not (og_identity or title_identity) else "mixed"
    elif candidate and og_identity and title_identity and candidate is og_identity:
        candidate = dict(og_identity)
        candidate["extraction_method"] = "mixed"
    elif candidate and candidate is title_identity and (og_identity or json_ld_identity):
        candidate = dict(title_identity)
        candidate["extraction_method"] = "mixed"

    if candidate and not candidate.get("artist"):
        artist_fallback = _extract_qobuz_artist_fallback(parser.meta, parser.title_text, candidate.get("title"))
        if artist_fallback:
            candidate = dict(candidate)
            candidate["artist"] = artist_fallback
            if candidate.get("extraction_method") != "mixed":
                candidate["extraction_method"] = "mixed"
            method_sources.add("artist_fallback")

    if not candidate:
        warnings.append("Не удалось найти Qobuz metadata в HTML.")

    return _finalize_identity(candidate, source_url, warnings, method_sources)


def extract_qobuz_release_identity(url):
    """Извлекает минимальную identity релиза из HTML Qobuz-страницы."""

    normalized_url = (url or "").strip()
    warnings = []
    parsed_url = urlparse(normalized_url)
    normalized_host = _normalize_host(parsed_url.netloc)
    open_qobuz_album_id = extract_open_qobuz_album_id(normalized_url)
    open_qobuz_warning = (
        "Open Qobuz links may not expose release metadata. Use a regular qobuz.com album page or TIDAL URL for full parsing."
    )

    if not _is_allowed_qobuz_url(normalized_url):
        warnings.append("Qobuz extraction доступен только для HTTP/HTTPS ссылок на qobuz.com.")
        return _finalize_identity(None, normalized_url, warnings, set())

    if normalized_host == "open.qobuz.com":
        warnings.append(open_qobuz_warning)

    identity = _extract_qobuz_identity_from_url(normalized_url)
    identity["source_url"] = normalized_url
    if normalized_host == "open.qobuz.com" and open_qobuz_warning not in identity.get("warnings", []):
        identity["warnings"] = [open_qobuz_warning] + identity.get("warnings", [])
    if open_qobuz_album_id:
        identity["qobuz_album_id"] = open_qobuz_album_id

    if _identity_has_release_fields(identity):
        return identity

    if open_qobuz_album_id:
        candidate_warnings = list(identity.get("warnings", []))
        candidate_warnings.append("Open Qobuz link did not expose release metadata.")

        for candidate_url in _build_open_qobuz_candidate_urls(open_qobuz_album_id):
            candidate_identity = _extract_qobuz_identity_from_url(candidate_url)
            if _identity_has_release_fields(candidate_identity):
                candidate_identity = dict(candidate_identity)
                candidate_identity["source_url"] = normalized_url
                candidate_identity["resolved_metadata_url"] = candidate_url
                candidate_identity["qobuz_album_id"] = open_qobuz_album_id
                candidate_identity["extraction_method"] = "{}_candidate".format(
                    candidate_identity.get("extraction_method") or "mixed"
                )
                candidate_identity["warnings"] = candidate_warnings + [
                    "Qobuz metadata was extracted via a candidate URL: {}.".format(candidate_url)
                ] + candidate_identity.get("warnings", [])
                return candidate_identity

        candidate_warnings.append("Tried Qobuz candidate URLs but release identity was not extracted.")
        identity["warnings"] = candidate_warnings

    if not identity.get("warnings"):
        identity["warnings"] = warnings

    return identity
