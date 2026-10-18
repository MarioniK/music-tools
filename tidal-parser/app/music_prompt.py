"""Данные релиза для промта проекта «Музыка», без правил оформления."""

from urllib.parse import urlparse


def release_year(result):
    value = result.get("release_year")
    if isinstance(value, bool):
        return None
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def release_type(result):
    value = str(result.get("release_kind") or result.get("entity_type") or "").lower()
    if value == "ep":
        return "EP"
    return value if value in {"album", "single", "track"} else None


def release_period(result):
    year = release_year(result)
    if year is None:
        return None
    if year < 2015:
        return "nostalgia"
    if year <= 2025:
        return "catalog"
    return "new" if year == 2026 else None


def _provider_url(result, domain, fields):
    for field in fields:
        value = result.get(field)
        if not isinstance(value, str):
            continue
        try:
            parsed = urlparse(value.strip())
            host = (parsed.hostname or "").lower()
        except ValueError:
            continue
        if parsed.scheme in {"http", "https"} and (host == domain or host.endswith("." + domain)):
            return value.strip()
    return None


def build_music_prompt(result):
    """Собирает одинаковый промт для TIDAL-результата и provider identity."""
    artist = result.get("artist") or "неизвестен"
    title = result.get("title") or "неизвестно"
    genres = result.get("final_genres") or result.get("genres") or []
    lines = [
        f"Исполнитель: {artist}",
        f"Название: {title}",
        f"Год: {release_year(result) or 'неизвестен'}",
        f"Дата релиза: {result.get('release_date') or result.get('mb_release_date') or 'неизвестна'}",
        f"Тип: {release_type(result) or 'неизвестен'}",
        f"Период: {release_period(result) or 'неизвестен'}",
    ]
    urls = [
        ("TIDAL", _provider_url(result, "tidal.com", ("source_url", "canonical_url"))),
        ("Qobuz", _provider_url(result, "qobuz.com", (
            "handoff_qobuz_url", "canonical_url", "source_url", "resolved_metadata_url", "handoff_qobuz_metadata_url",
        ))),
    ]
    available_urls = [f"{label}: {url}" for label, url in urls if url]
    if available_urls:
        lines.extend(["", *available_urls])
    lines.extend([
        "",
        f"Черновые жанры: {', '.join(genres) or '—'}",
        f"Страна: {result.get('country') or '—'}",
        f"Черновые теги: {(result.get('blog_output') or {}).get('line2') or '—'}",
    ])
    tasks = result.get("additional_tasks")
    if isinstance(tasks, str) and tasks.strip():
        lines.extend(["", "Дополнительные задачи:", tasks.strip()])
    elif isinstance(tasks, (list, tuple)):
        task_lines = [f"- {task.strip()}" for task in tasks if isinstance(task, str) and task.strip()]
        if task_lines:
            lines.extend(["", "Дополнительные задачи:", *task_lines])
    lines.extend(["", "Правила оформления и источников: по инструкциям проекта"])
    return "\n".join(lines)
