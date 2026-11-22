"""Общие подмены для тестов форм: поиск кандидатов TIDAL и build_result."""

from app import main


def patch_lookup(monkeypatch, result, expected_args=None):
    """lookup_tidal_candidates всегда возвращает `result`; expected_args = (artist, title, release_type, year)."""

    async def fake_lookup(artist=None, title=None, release_type=None, year=None, *args, **kwargs):
        if expected_args is not None:
            assert (artist, title, release_type, year) == expected_args
        return result

    monkeypatch.setattr(main, "lookup_tidal_candidates", fake_lookup)


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
