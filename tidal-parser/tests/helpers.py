"""Общие подмены для тестов форм: поиск кандидатов TIDAL и build_result."""

from app import main


def patch_lookup(monkeypatch, result, expected_args=None):
    """lookup_tidal_candidates всегда возвращает `result`; expected_args = (artist, title, release_type, year).

    Возвращает список вызовов [(artist, title, release_type, year), ...].
    """
    calls = []

    async def fake_lookup(artist=None, title=None, release_type=None, year=None, *args, **kwargs):
        calls.append((artist, title, release_type, year))
        if expected_args is not None:
            assert (artist, title, release_type, year) == expected_args
        return result

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)
    return calls


def forbid_lookup(monkeypatch, message):
    """Любой вызов lookup_tidal_candidates -> AssertionError(message)."""

    async def forbidden_lookup(*args, **kwargs):
        raise AssertionError(message)

    monkeypatch.setattr(main, "lookup_tidal_candidates", forbidden_lookup)


def patch_build_result(monkeypatch, handoff=None, error=None, forbid=None):
    """Подменяет build_result: handoff(url) -> результат, error -> исключение, forbid -> AssertionError.

    Возвращает {"url": последний url, "called": был ли вызов}.
    """
    captured = {"url": None, "called": False}

    async def fake_build_result(url, force_refresh=False, baseline=None):
        captured["url"] = url
        captured["called"] = True
        if forbid:
            raise AssertionError(forbid)
        if error:
            raise error
        return handoff(url)

    monkeypatch.setattr(main, "build_result", fake_build_result)
    return captured


def tidal_candidate(
    candidate_id,
    title,
    release_date,
    year,
    tidal_url,
    score,
    candidate_type="album",
    is_best_candidate=True,
    score_reasons=None,
):
    return {
        "id": candidate_id,
        "type": candidate_type,
        "title": title,
        "release_date": release_date,
        "year": year,
        "source_relation": "tracks" if candidate_type == "track" else "albums",
        "tidal_url": tidal_url,
        "display_line": "{} ({}) [{}]".format(title, release_date or year or "—", candidate_type),
        "score": score,
        "score_reasons": score_reasons or [],
        "is_best_candidate": is_best_candidate,
    }


def tidal_lookup_result(candidates, release_type, query="Candidate lookup"):
    best_candidate = candidates[0] if candidates else None
    match_state = "strong" if best_candidate and (best_candidate.get("score") or 0) >= 75 else "weak"
    if not candidates:
        match_state = "empty"

    return {
        "state": "success",
        "message": None,
        "query": query,
        "release_type": release_type,
        "candidates": candidates,
        "tidal_candidates_best_score": best_candidate.get("score") if best_candidate else None,
        "tidal_candidates_best_candidate": best_candidate,
        "tidal_candidates_match_state": match_state,
    }


def tidal_handoff_result(url, artist, title, release_year, entity_type, release_kind):
    return {
        "source_url": url,
        "entity_type": entity_type,
        "tidal_id": "498548519",
        "artist": artist,
        "title": title,
        "album": None,
        "release_kind": release_kind,
        "release_year": release_year,
        "country": "—",
        "genres": [],
        "final_genres": [],
        "audio_genres_raw": [],
        "audio_genres_pretty": [],
        "blog_output": {
            "line1": "{} — «{}»{}".format(
                artist,
                title,
                " ({})".format(release_year) if entity_type != "track" and release_year is not None else "",
            ),
            "line2": "#music #music2026",
        },
        "source_name": "tidal",
        "meta_source_url": url,
        "note": None,
        "from_cache": False,
    }
