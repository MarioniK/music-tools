from bs4 import BeautifulSoup
import pytest

from app import main
from app.music_prompt import build_music_prompt, release_period


def release(**overrides):
    result = {
        "artist": "Test Artist",
        "title": "Test Release",
        "release_year": 2026,
        "release_kind": "album",
        "entity_type": "album",
        "country": "Великобритания",
        "artist_country_tag": "british",
        "final_genres": ["R&B", "drum & bass", "rock and roll"],
    }
    result.update(overrides)
    result["blog_output"] = main.build_blog_output(result)
    return result


@pytest.mark.parametrize("kind,year,expected", [
    ("album", 2014, "#longplay #nostalgie"),
    ("album", 2015, "#longplay"),
    ("album", 2025, "#longplay"),
    ("album", 2026, "#newrelease #newalbum"),
    ("ep", 2014, "#ep #nostalgie"),
    ("ep", 2015, "#ep"),
    ("ep", 2025, "#ep"),
    ("ep", 2026, "#newrelease #newep"),
    ("single", 2014, "#nostalgie"),
    ("single", 2015, ""),
    ("single", 2025, ""),
    ("single", 2026, "#newrelease #dailylist"),
    ("track", 2014, "#nostalgie"),
    ("track", 2015, ""),
    ("track", 2025, ""),
    ("track", 2026, "#newrelease #dailylist"),
])
def test_draft_tags_follow_project_type_and_period(kind, year, expected):
    result = release(release_kind=kind, release_year=year)
    prefix = f"#music #music{year} #testartist #british #rnb #drumnbass #rocknroll #djdrugfm"
    assert result["blog_output"]["line2"] == " ".join(filter(None, [prefix, expected, "#омузыке"]))


@pytest.mark.parametrize("year,expected", [(2014, "nostalgia"), ("2015", "catalog"), (2025, "catalog"), (2026, "new"), (2027, None), (None, None), (True, None)])
def test_release_period_boundaries(year, expected):
    assert release_period({"release_year": year}) == expected


def test_prompt_keeps_data_and_actual_provider_urls():
    result = release(
        source_url="https://tidal.com/album/123",
        handoff_qobuz_url="https://www.qobuz.com/us-en/album/test/123",
        mb_release_date="2026-03-06",
        additional_tasks=["Сравнить с предыдущим альбомом."],
    )
    prompt = build_music_prompt(result)
    assert "Дата релиза: 2026-03-06" in prompt
    assert "TIDAL: https://tidal.com/album/123" in prompt
    assert "Qobuz: https://www.qobuz.com/us-en/album/test/123" in prompt
    assert "Дополнительные задачи:\n- Сравнить с предыдущим альбомом." in prompt
    assert prompt.count("site:dtf.ru") == 4
    assert prompt.endswith("Правила оформления и источников: по промту проекта")
    for instruction in ("Найди Qobuz review", "Сделай вывод", "Стоп-лист", "Собери каркас", "Не использовать запрещённые"):
        assert instruction not in prompt


def test_qobuz_identity_is_not_labelled_tidal():
    result = release(source_url="https://www.qobuz.com/us-en/album/test/123", release_year=None)
    prompt = build_music_prompt(result)
    assert "TIDAL:" not in prompt
    assert "Qobuz: https://www.qobuz.com/us-en/album/test/123" in prompt
    assert "Период: неизвестен" in prompt
    assert "Дополнительные задачи:" not in prompt


def test_both_ui_branches_render_identical_prompt_and_escape_html():
    result = release(artist="Artist <script>alert(1)</script>")
    template = main.templates.env.get_template("index.html")
    prompts = []
    for state in ("extracted_release_identity", None):
        rendered = template.render(result=dict(result, input_state=state))
        soup = BeautifulSoup(rendered, "html.parser")
        target = soup.find("textarea", id="music-prompt-copy-target")
        assert target is not None
        assert target.find("script") is None
        prompts.append(target.get_text())
    assert prompts[0] == prompts[1] == build_music_prompt(result)


def test_genre_fallback_deduplicates_tags():
    result = release(final_genres=[], genres=["R&B", "R and B", "indie-rock"])
    assert result["blog_output"]["line2"].count("#rnb") == 1
    assert "#indierock" in result["blog_output"]["line2"]
