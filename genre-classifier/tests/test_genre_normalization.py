import pytest

from app.genre_normalization import (
    genre_to_blog_tag,
    normalize_audio_prediction_genres,
    normalize_genre_value,
    normalize_genres,
)


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


def test_normalize_audio_prediction_genres_normalizes_variants():
    raw = [
        {"tag": "Indie Rock", "prob": 0.9},
        {"tag": "dream-pop", "prob": 0.8},
        {"tag": "indie-rock", "prob": 0.7},
    ]

    assert normalize_audio_prediction_genres(raw, min_prob=0.05) == [
        "indie rock",
        "dream pop",
    ]


def test_normalize_audio_prediction_genres_filters_non_genre_descriptors():
    raw = [
        {"tag": "female vocalists", "prob": 0.9},
        {"tag": "Indie Rock", "prob": 0.8},
    ]

    assert normalize_audio_prediction_genres(raw, min_prob=0.05) == [
        "indie rock",
    ]
