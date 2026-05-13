"""Извлечение минимальной identity релиза из Apple Music HTML-страницы."""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener


MAX_APPLE_MUSIC_HTML_BYTES = 1024 * 1024
APPLE_MUSIC_FETCH_TIMEOUT_SECONDS = 5
APPLE_MUSIC_USER_AGENT = "music-tools/1.0 (+https://github.com/MarioniK/music-tools)"

_ALLOWED_APPLE_MUSIC_HOSTS = {"music.apple.com"}
_GENERIC_APPLE_TITLES = {
    "apple music web player",
    "apple music",
}
_GENERIC_APPLE_ARTISTS = {
    "apple music web player",
    "apple music",
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


def _is_allowed_apple_music_host(host: str) -> bool:
    if not host:
        return False
    if host in _ALLOWED_APPLE_MUSIC_HOSTS:
        return True
    return host.endswith(".apple.com")


def _is_allowed_apple_music_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return _is_allowed_apple_music_host(_normalize_host(parsed.netloc))


def _parse_date(value):
    cleaned = _clean_text(value)
    if not cleaned:
        return None

    if re.match(r"^\d{4}-\d{2}-\d{2}", cleaned):
        return cleaned[:10]

    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue

    return None


def _extract_provider_item_id(url: str):
    parsed = urlparse((url or "").strip())
    if _normalize_host(parsed.netloc) != "music.apple.com":
        return None

    path = parsed.path or ""
    patterns = [
        r"/(?:album|song)/[^/?#]+/(\d+)(?:[/?#]|$)",
        r"/(?:album|song)/(\d+)(?:[/?#]|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, path)
        if match:
            return match.group(1)

    return None


def _extract_title_artist(title_source):
    cleaned = _clean_text(title_source)
    if not cleaned:
        return None, None

    if cleaned.lower() in _GENERIC_APPLE_TITLES:
        return None, None

    patterns = [
        r"^(?P<title>.+?)\s+by\s+(?P<artist>.+?)\s+on\s+Apple\s+Music$",
        r"^(?P<title>.+?)\s+by\s+(?P<artist>.+?)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            title = _clean_text(match.group("title"))
            artist = _clean_text(match.group("artist"))
            if title and artist:
                return artist, title

    return None, cleaned


def _extract_name(value):
    if isinstance(value, dict):
        nested_name = value.get("name")
        if nested_name is not None:
            nested = _extract_name(nested_name)
            if nested:
                return nested
        for key in ("byArtist", "artist", "creator", "@graph", "@list"):
            nested = _extract_name(value.get(key))
            if nested:
                return nested
        return None

    if isinstance(value, list):
        for item in value:
            nested = _extract_name(item)
            if nested:
                return nested
        return None

    cleaned = _clean_text(value)
    if cleaned and cleaned.lower() not in _GENERIC_APPLE_ARTISTS:
        return cleaned

    return None


def _json_ld_release_type(types):
    type_set = {item.lower() for item in types if item}
    if "musicalbum" in type_set:
        return "album"
    if "musiccomposition" in type_set or "musicrecording" in type_set:
        return "track"
    return None


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
        "artist": _extract_name(obj.get("byArtist") or obj.get("artist") or obj.get("creator")),
        "title": _clean_text(obj.get("name")),
        "year": None,
        "release_date": None,
        "release_type": release_type,
        "primary_source": "json_ld",
        "extraction_method": "json_ld",
    }

    release_date = _parse_date(obj.get("datePublished") or obj.get("releaseDate") or obj.get("dateCreated"))
    if release_date:
        candidate["release_date"] = release_date
        candidate["year"] = int(release_date[:4])

    score = 0
    if candidate["title"]:
        score += 10
    if candidate["artist"]:
        score += 10
    if candidate["release_date"]:
        score += 5
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

    return best_candidate


def _build_open_graph_identity(meta):
    title_source = meta.get("og:title") or meta.get("twitter:title") or meta.get("title")
    if not title_source:
        return None

    artist, title = _extract_title_artist(title_source)
    if not artist and not title:
        return None

    release_type_source = _clean_text(meta.get("og:type") or "") or ""
    if "album" in release_type_source.lower():
        release_type = "album"
    elif "song" in release_type_source.lower() or "track" in release_type_source.lower():
        release_type = "track"
    else:
        release_type = None

    candidate = {
        "artist": artist,
        "title": title or artist,
        "year": None,
        "release_date": None,
        "release_type": release_type,
        "primary_source": "open_graph" if meta.get("og:title") else "twitter_card",
        "extraction_method": "open_graph" if meta.get("og:title") else "twitter_card",
    }

    release_date = _parse_date(meta.get("music:release_date"))
    if release_date:
        candidate["release_date"] = release_date
        candidate["year"] = int(release_date[:4])

    return candidate


def _build_html_title_identity(title_text):
    artist, title = _extract_title_artist(title_text)
    if not artist and not title:
        return None

    return {
        "artist": artist,
        "title": title,
        "year": None,
        "release_date": None,
        "release_type": None,
        "primary_source": "html_title",
        "extraction_method": "html_title",
    }


def _merge_candidates(candidates):
    merged = {}
    primary_source = None
    method_sources = set()

    for candidate in candidates:
        if not candidate:
            continue

        method_sources.add(candidate.get("extraction_method") or "mixed")
        if not primary_source:
            primary_source = candidate.get("primary_source") or candidate.get("extraction_method")

        for key in ("artist", "title", "year", "release_date", "release_type"):
            if merged.get(key) in (None, "") and candidate.get(key) not in (None, ""):
                merged[key] = candidate.get(key)

    if not merged:
        return None, set()

    if len(method_sources) > 1:
        merged["extraction_method"] = "mixed"
    else:
        merged["extraction_method"] = next(iter(method_sources))

    merged["primary_source"] = primary_source or merged["extraction_method"]
    return merged, method_sources


class _AppleMusicHTMLMetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_text = ""
        self._in_title = False
        self._in_json_ld = False
        self._json_ld_buffer = []
        self.meta = {}
        self.canonical_url = None
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

        if tag == "link":
            rel = (attrs.get("rel") or "").lower()
            if "canonical" in rel and attrs.get("href"):
                self.canonical_url = attrs.get("href").strip()
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


def _fetch_apple_music_html(url):
    request = Request(
        url,
        headers={
            "User-Agent": APPLE_MUSIC_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    opener = build_opener()
    warnings = []

    try:
        with opener.open(request, timeout=APPLE_MUSIC_FETCH_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            raw_html = response.read(MAX_APPLE_MUSIC_HTML_BYTES + 1)
            truncated = len(raw_html) > MAX_APPLE_MUSIC_HTML_BYTES
            if truncated:
                raw_html = raw_html[:MAX_APPLE_MUSIC_HTML_BYTES]
                warnings.append("Apple Music HTML was truncated to 1 MB.")

            charset = response.headers.get_content_charset() or "utf-8"
            html_text = raw_html.decode(charset, errors="replace")
            return html_text, content_type, final_url, warnings
    except HTTPError as exc:
        body = b""
        if exc.fp is not None:
            try:
                body = exc.fp.read(MAX_APPLE_MUSIC_HTML_BYTES + 1)
            except Exception:
                body = b""

        if len(body) > MAX_APPLE_MUSIC_HTML_BYTES:
            body = body[:MAX_APPLE_MUSIC_HTML_BYTES]
            warnings.append("Apple Music HTML was truncated to 1 MB.")

        charset = getattr(getattr(exc, "headers", None), "get_content_charset", lambda: None)() or "utf-8"
        html_text = body.decode(charset, errors="replace") if body else ""
        if body:
            warnings.append("Apple Music request returned HTTP {}.".format(getattr(exc, "code", "error")))
        return html_text, getattr(exc, "headers", {}).get("Content-Type", ""), getattr(exc, "geturl", lambda: url)(), warnings
    except URLError:
        warnings.append("Не удалось загрузить Apple Music страницу.")
        return "", "", url, warnings


def _build_identity_from_html(html_text, source_url, final_url=None):
    parser = _AppleMusicHTMLMetadataParser()
    parser.feed(html_text or "")
    parser.close()

    json_ld_candidate = _build_json_ld_identity(parser.json_ld_blocks)
    og_candidate = _build_open_graph_identity(parser.meta)
    title_candidate = _build_html_title_identity(parser.title_text)

    merged, method_sources = _merge_candidates([json_ld_candidate, og_candidate, title_candidate])

    warnings = []
    if not merged:
        warnings.append("Не удалось извлечь metadata Apple Music.")
        merged = {}

    canonical_url = _clean_text(parser.canonical_url or parser.meta.get("og:url") or final_url or source_url)
    if canonical_url:
        merged["resolved_metadata_url"] = canonical_url
        merged["canonical_url"] = canonical_url

    provider_item_id = _extract_provider_item_id(canonical_url or final_url or source_url)
    if provider_item_id:
        merged["provider_item_id"] = provider_item_id

    if not merged.get("release_type"):
        path = urlparse((canonical_url or final_url or source_url or "").strip()).path
        if "/album/" in path:
            merged["release_type"] = "album"
        elif "/song/" in path:
            merged["release_type"] = "track"

    if merged.get("release_date") and not merged.get("year"):
        merged["year"] = int(merged["release_date"][:4])

    if merged.get("artist") and merged.get("title"):
        if merged.get("release_type") and merged.get("year"):
            confidence = "high"
        elif len(method_sources) > 1:
            confidence = "high"
        else:
            confidence = "medium"
    elif merged.get("title"):
        confidence = "low" if not merged.get("artist") else "medium"
    else:
        confidence = "low"

    if merged.get("artist") and merged.get("artist").lower() in _GENERIC_APPLE_ARTISTS:
        merged["artist"] = None
    if merged.get("title") and merged.get("title").lower() in _GENERIC_APPLE_TITLES:
        merged["title"] = None

    if not merged.get("artist") and not merged.get("title"):
        warnings.append("Apple Music page metadata found, but artist/title were not identified.")

    if not merged.get("release_type"):
        warnings.append("Apple Music release type was not identified.")

    if not merged.get("release_date") and not merged.get("year"):
        warnings.append("Apple Music release date was not identified.")

    if not merged.get("provider_item_id"):
        warnings.append("Apple Music provider item id was not identified.")

    if merged.get("artist") and merged.get("title"):
        if merged.get("release_type") == "album":
            extraction_method = merged.get("extraction_method", "mixed")
        elif merged.get("release_type") == "track":
            extraction_method = merged.get("extraction_method", "mixed")
        else:
            extraction_method = merged.get("extraction_method", "mixed")
    else:
        extraction_method = "none"

    identity = {
        "input_state": "extracted_release_identity",
        "provider": "apple_music",
        "provider_label": "Apple Music",
        "source_url": source_url,
        "resolved_metadata_url": merged.get("resolved_metadata_url"),
        "canonical_url": merged.get("canonical_url"),
        "provider_item_id": merged.get("provider_item_id"),
        "artist": merged.get("artist"),
        "title": merged.get("title"),
        "year": merged.get("year"),
        "release_date": merged.get("release_date"),
        "release_type": merged.get("release_type"),
        "cover_url": merged.get("cover_url"),
        "extraction_method": extraction_method,
        "primary_source": merged.get("primary_source"),
        "confidence": confidence,
        "warnings": warnings,
    }

    if not identity["artist"] and not identity["title"]:
        identity["release_type"] = None
        identity["year"] = None
        identity["release_date"] = None
        identity["provider_item_id"] = merged.get("provider_item_id")

    return identity


def parse_apple_music_release_identity_from_html(html_text, source_url, final_url=None):
    """Парсит Apple Music HTML и возвращает нормализованную identity релиза."""

    normalized_source_url = _clean_text(source_url)
    if not normalized_source_url:
        return {
            "input_state": "extracted_release_identity",
            "provider": "apple_music",
            "provider_label": "Apple Music",
            "source_url": source_url,
            "resolved_metadata_url": None,
            "canonical_url": None,
            "provider_item_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": ["Не удалось извлечь metadata Apple Music."],
        }

    return _build_identity_from_html(html_text, normalized_source_url, final_url=final_url)


def extract_apple_music_release_identity(url):
    """Извлекает minimal identity релиза из публичной Apple Music ссылки."""

    normalized_url = _clean_text(url)
    if not normalized_url:
        return parse_apple_music_release_identity_from_html("", url)

    warnings = []
    if not _is_allowed_apple_music_url(normalized_url):
        warnings.append("Apple Music extraction доступен только для HTTP/HTTPS ссылок на music.apple.com.")
        return {
            "input_state": "extracted_release_identity",
            "provider": "apple_music",
            "provider_label": "Apple Music",
            "source_url": normalized_url,
            "resolved_metadata_url": None,
            "canonical_url": None,
            "provider_item_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": warnings,
        }

    html_text, _content_type, final_url, fetch_warnings = _fetch_apple_music_html(normalized_url)
    warnings.extend(fetch_warnings)
    if not html_text:
        return {
            "input_state": "extracted_release_identity",
            "provider": "apple_music",
            "provider_label": "Apple Music",
            "source_url": normalized_url,
            "resolved_metadata_url": None,
            "canonical_url": None,
            "provider_item_id": None,
            "artist": None,
            "title": None,
            "year": None,
            "release_date": None,
            "release_type": None,
            "cover_url": None,
            "extraction_method": "none",
            "primary_source": None,
            "confidence": "low",
            "warnings": warnings or ["Не удалось извлечь metadata Apple Music."],
        }

    identity = parse_apple_music_release_identity_from_html(html_text, normalized_url, final_url=final_url)
    if warnings:
        identity["warnings"] = warnings + identity.get("warnings", [])
    if final_url and not identity.get("resolved_metadata_url"):
        identity["resolved_metadata_url"] = final_url
        identity["canonical_url"] = final_url
    return identity
