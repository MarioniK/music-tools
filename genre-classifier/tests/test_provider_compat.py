import pytest

from app.providers.compat import (
    map_validated_result_to_legacy_genres,
    map_validated_result_to_legacy_genres_pretty,
)
from app.providers.schema import ValidatedGenreItem, ValidatedProviderResult


def test_map_validated_result_to_legacy_genres_returns_legacy_shape():
    validated_result = ValidatedProviderResult(
        genres=[ValidatedGenreItem(tag="indie rock", score=0.81234)],
        provider_name="stub",
        model_name="stub-v1",
        total_items_received=1,
        total_items_kept=1,
        dropped_items_count=0,
    )

    result = map_validated_result_to_legacy_genres(validated_result)

    assert result == [{"tag": "indie rock", "prob": 0.8123}]


def test_map_validated_result_to_legacy_genres_rounds_prob_to_four_digits():
    validated_result = ValidatedProviderResult(
        genres=[ValidatedGenreItem(tag="dream pop", score=0.123456)],
        provider_name="stub",
        model_name=None,
        total_items_received=1,
        total_items_kept=1,
        dropped_items_count=0,
    )

    result = map_validated_result_to_legacy_genres(validated_result)

    assert result == [{"tag": "dream pop", "prob": 0.1235}]


def test_map_validated_result_to_legacy_genres_preserves_order():
    validated_result = ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="genre b", score=0.9),
            ValidatedGenreItem(tag="genre a", score=0.8),
            ValidatedGenreItem(tag="genre c", score=0.7),
        ],
        provider_name="stub",
        model_name=None,
        total_items_received=3,
        total_items_kept=3,
        dropped_items_count=0,
    )

    result = map_validated_result_to_legacy_genres(validated_result)

    assert result == [
        {"tag": "genre b", "prob": 0.9},
        {"tag": "genre a", "prob": 0.8},
        {"tag": "genre c", "prob": 0.7},
    ]


def test_map_validated_result_to_legacy_genres_pretty_uses_normalization_pipeline(monkeypatch):
    validated_result = ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="Indie Rock", score=0.81234),
            ValidatedGenreItem(tag="female vocalists", score=0.7),
            ValidatedGenreItem(tag="dream-pop", score=0.0499),
        ],
        provider_name="stub",
        model_name=None,
        total_items_received=3,
        total_items_kept=3,
        dropped_items_count=0,
    )
    captured = {}

    def fake_normalize_audio_prediction_genres(raw_genres, min_prob=0.05):
        captured["raw_genres"] = raw_genres
        captured["min_prob"] = min_prob
        return ["indie rock"]

    monkeypatch.setattr(
        "app.providers.compat.normalize_audio_prediction_genres",
        fake_normalize_audio_prediction_genres,
    )

    result = map_validated_result_to_legacy_genres_pretty(validated_result)

    assert result == ["indie rock"]
    assert captured["raw_genres"] == [
        {"tag": "Indie Rock", "prob": 0.8123},
        {"tag": "female vocalists", "prob": 0.7},
        {"tag": "dream-pop", "prob": 0.0499},
    ]
    assert captured["min_prob"] == 0.05


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        "not-a-validated-result",
        {"genres": []},
    ],
)
def test_map_validated_result_to_legacy_genres_rejects_invalid_input(invalid_value):
    with pytest.raises(RuntimeError, match="invalid validated result"):
        map_validated_result_to_legacy_genres(invalid_value)


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        "not-a-validated-result",
        {"genres": []},
    ],
)
def test_map_validated_result_to_legacy_genres_pretty_rejects_invalid_input(invalid_value):
    with pytest.raises(RuntimeError, match="invalid validated result"):
        map_validated_result_to_legacy_genres_pretty(invalid_value)
