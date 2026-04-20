import math

import pytest

from app.providers.base import ProviderGenreScore, ProviderResult
from app.providers.schema import ValidatedGenreItem, ValidatedProviderResult
from app.providers.validation import validate_and_normalize_provider_result


def test_validate_and_normalize_provider_result_accepts_valid_result():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="Indie Rock", score=0.9),
            ProviderGenreScore(tag="Dream Pop", score=0.7),
        ],
        provider_name="stub",
        model_name="stub-v1",
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert isinstance(result, ValidatedProviderResult)
    assert result == ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="indie rock", score=0.9),
            ValidatedGenreItem(tag="dream pop", score=0.7),
        ],
        provider_name="stub",
        model_name="stub-v1",
        total_items_received=2,
        total_items_kept=2,
        dropped_items_count=0,
    )


def test_validate_and_normalize_provider_result_normalizes_tag():
    provider_result = ProviderResult(
        genres=[ProviderGenreScore(tag="  Synth-Pop__Wave  ", score=0.8)],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [ValidatedGenreItem(tag="synth pop wave", score=0.8)]


def test_validate_and_normalize_provider_result_drops_empty_tag():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="___---   ", score=0.8),
            ProviderGenreScore(tag="indie rock", score=0.5),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [ValidatedGenreItem(tag="indie rock", score=0.5)]
    assert result.total_items_received == 2
    assert result.total_items_kept == 1
    assert result.dropped_items_count == 1


def test_validate_and_normalize_provider_result_drops_non_numeric_score():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="indie rock", score="oops"),
            ProviderGenreScore(tag="dream pop", score=0.5),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [ValidatedGenreItem(tag="dream pop", score=0.5)]


def test_validate_and_normalize_provider_result_drops_nan_and_inf_scores():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="indie rock", score=math.nan),
            ProviderGenreScore(tag="dream pop", score=math.inf),
            ProviderGenreScore(tag="shoegaze", score=-math.inf),
            ProviderGenreScore(tag="post punk", score=0.4),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [ValidatedGenreItem(tag="post punk", score=0.4)]


def test_validate_and_normalize_provider_result_keeps_max_score_for_duplicate_tags():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="Indie Rock", score=0.4),
            ProviderGenreScore(tag="indie-rock", score=0.9),
            ProviderGenreScore(tag="indie_rock", score=0.7),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [ValidatedGenreItem(tag="indie rock", score=0.9)]
    assert result.total_items_received == 3
    assert result.total_items_kept == 1
    assert result.dropped_items_count == 2


def test_validate_and_normalize_provider_result_sorts_deterministically():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="zeta", score=0.9),
            ProviderGenreScore(tag="alpha", score=0.9),
            ProviderGenreScore(tag="beta", score=1.0),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result)

    assert result.genres == [
        ValidatedGenreItem(tag="beta", score=1.0),
        ValidatedGenreItem(tag="alpha", score=0.9),
        ValidatedGenreItem(tag="zeta", score=0.9),
    ]


def test_validate_and_normalize_provider_result_applies_top_n_after_sorting():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="genre c", score=0.7),
            ProviderGenreScore(tag="genre a", score=0.9),
            ProviderGenreScore(tag="genre b", score=0.8),
        ],
        provider_name="stub",
        model_name=None,
    )

    result = validate_and_normalize_provider_result(provider_result, top_n=2)

    assert result.genres == [
        ValidatedGenreItem(tag="genre a", score=0.9),
        ValidatedGenreItem(tag="genre b", score=0.8),
    ]
    assert result.total_items_received == 3
    assert result.total_items_kept == 2
    assert result.dropped_items_count == 1


def test_validate_and_normalize_provider_result_raises_for_zero_top_n():
    provider_result = ProviderResult(
        genres=[ProviderGenreScore(tag="indie rock", score=0.9)],
        provider_name="stub",
        model_name=None,
    )

    with pytest.raises(RuntimeError, match="invalid top_n"):
        validate_and_normalize_provider_result(provider_result, top_n=0)


def test_validate_and_normalize_provider_result_raises_for_negative_top_n():
    provider_result = ProviderResult(
        genres=[ProviderGenreScore(tag="indie rock", score=0.9)],
        provider_name="stub",
        model_name=None,
    )

    with pytest.raises(RuntimeError, match="invalid top_n"):
        validate_and_normalize_provider_result(provider_result, top_n=-1)


def test_validate_and_normalize_provider_result_raises_for_non_integer_top_n():
    provider_result = ProviderResult(
        genres=[ProviderGenreScore(tag="indie rock", score=0.9)],
        provider_name="stub",
        model_name=None,
    )

    with pytest.raises(RuntimeError, match="invalid top_n"):
        validate_and_normalize_provider_result(provider_result, top_n="2")


def test_validate_and_normalize_provider_result_raises_for_fully_invalid_output():
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="   ", score=0.9),
            ProviderGenreScore(tag="indie rock", score=math.nan),
            "not-a-provider-genre-score",
        ],
        provider_name="stub",
        model_name=None,
    )

    with pytest.raises(RuntimeError, match="no valid provider genres"):
        validate_and_normalize_provider_result(provider_result)
