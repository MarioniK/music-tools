import pytest

from app.genre_normalization import genre_to_blog_tag, normalize_genre_value, normalize_genres
from app.main import merge_final_genres


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("Indie Rock", "indie rock"),
        ("indie-rock", "indie rock"),
        (" indie   rock ", "indie rock"),
    ],
)
def test_normalize_genre_value(raw_value, expected):
    assert normalize_genre_value(raw_value) == expected


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (["Indie Rock", "indie-rock", " dream pop "], ["indie rock", "dream pop"]),
        ("indie rock, dream pop", ["indie rock", "dream pop"]),
        ("indie rock / dream pop", ["indie rock", "dream pop"]),
        ("indie rock; dream pop", ["indie rock", "dream pop"]),
        (["dream pop", "indie rock", "dream-pop"], ["dream pop", "indie rock"]),
    ],
)
def test_normalize_genres(raw_value, expected):
    assert normalize_genres(raw_value) == expected


def test_normalize_genres_preserves_first_occurrence_order():
    assert normalize_genres(["dream pop", "indie rock", "dream-pop", "indie rock"]) == [
        "dream pop",
        "indie rock",
    ]


def test_normalize_genres_is_idempotent():
    value = ["Indie Rock", "indie-rock", " dream pop ", "indie rock / dream-pop"]
    normalized = normalize_genres(value)
    assert normalize_genres(normalized) == normalized


def test_genre_to_blog_tag():
    assert genre_to_blog_tag("indie rock") == "indierock"
    assert genre_to_blog_tag("dream pop") == "dreampop"
    assert genre_to_blog_tag("post punk") == "postpunk"


def test_merge_final_genres_deduplicates_equivalent_variants_stably():
    merged = merge_final_genres(
        ["Indie Rock", "dream-pop"],
        ["indie-rock", " dream pop "],
        "track",
    )

    assert merged == ["indie rock", "dream pop"]


def test_non_genre_descriptors_do_not_reach_final_genres_or_blog_output():
    from app.main import build_blog_output

    merged = merge_final_genres(
        ["rock"],
        ["female vocalists", "indie rock"],
        "track",
    )

    result = {
        "artist": "Artist",
        "title": "Title",
        "entity_type": "track",
        "release_year": 2024,
        "artist_country_tag": "american",
        "final_genres": merged,
    }
    blog_output = build_blog_output(result)

    assert "female vocalists" not in merged
    assert "indie rock" in merged
    assert "#femalevocalists" not in blog_output["line2"]
    assert "#indierock" in blog_output["line2"]
