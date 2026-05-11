"""Определение типа музыкального пользовательского ввода."""

from __future__ import annotations

import re
from urllib.parse import urlparse


_URL_PROVIDERS = (
    ("tidal", {"tidal.com"}),
    ("qobuz", {"qobuz.com"}),
    ("spotify", {"open.spotify.com"}),
    ("apple_music", {"music.apple.com"}),
    ("yandex_music", {"music.yandex.ru", "music.yandex.com"}),
)

_MANUAL_RELEASE_RE = re.compile(
    r"""
    ^\s*
    (?P<artist>.+?)
    \s*(?:—|-)\s*
    (?P<title>
        «[^»]+»
        |
        "[^"]+"
        |
        [^()]+?
    )
    (?:\s*\((?P<year>\d{4})\))?
    \s*$
    """,
    re.VERBOSE,
)


def _normalize_input(raw_input: str) -> str:
    if raw_input is None:
        return ""
    return re.sub(r"\s+", " ", str(raw_input)).strip()


def _normalize_host(netloc: str) -> str:
    host = (netloc or "").lower().strip()
    if ":" in host:
        host = host.split(":", 1)[0]
    return host


def _detect_url_provider(normalized_input: str) -> str:
    parsed = urlparse(normalized_input)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "unknown"

    host = _normalize_host(parsed.netloc)
    for provider, hosts in _URL_PROVIDERS:
        for candidate in hosts:
            if host == candidate or host.endswith("." + candidate):
                return provider

    return "unknown"


def _strip_wrapping_quotes(value: str) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) >= 2:
        if cleaned[0] == "«" and cleaned[-1] == "»":
            return cleaned[1:-1].strip()
        if cleaned[0] == '"' and cleaned[-1] == '"':
            return cleaned[1:-1].strip()
    return cleaned


def _detect_manual_release_line(normalized_input: str):
    match = _MANUAL_RELEASE_RE.match(normalized_input)
    if not match:
        return None

    artist = (match.group("artist") or "").strip()
    title = _strip_wrapping_quotes(match.group("title"))
    year = match.group("year")

    if not artist or not title:
        return None

    result = {
        "input_type": "manual_release_line",
        "provider": "manual",
        "raw_input": normalized_input,
        "normalized_input": normalized_input,
        "artist": artist,
        "title": title,
        "year": int(year) if year else None,
        "confidence": "high",
        "warnings": [],
    }
    return result


def detect_music_input(raw_input: str):
    """Определяет тип музыкального ввода без обращения к внешним сервисам."""

    normalized_input = _normalize_input(raw_input)
    if not normalized_input:
        return {
            "input_type": "unknown",
            "provider": "unknown",
            "raw_input": raw_input,
            "normalized_input": normalized_input,
            "artist": None,
            "title": None,
            "year": None,
            "confidence": "low",
            "warnings": ["Пустой ввод."],
        }

    if normalized_input.startswith(("http://", "https://")):
        provider = _detect_url_provider(normalized_input)
        warnings = []
        if provider == "unknown":
            warnings = ["Неподдерживаемый URL провайдер."]

        return {
            "input_type": "url",
            "provider": provider,
            "raw_input": raw_input,
            "normalized_input": normalized_input,
            "artist": None,
            "title": None,
            "year": None,
            "confidence": "medium" if provider != "unknown" else "low",
            "warnings": warnings,
        }

    manual_release = _detect_manual_release_line(normalized_input)
    if manual_release:
        manual_release["raw_input"] = raw_input
        return manual_release

    return {
        "input_type": "unknown",
        "provider": "unknown",
        "raw_input": raw_input,
        "normalized_input": normalized_input,
        "artist": None,
        "title": None,
        "year": None,
        "confidence": "low",
        "warnings": [
            "Не удалось распознать ссылку или ручную строку релиза.",
        ],
    }
