from types import SimpleNamespace

from app.genres.postprocessing import postprocess_llm_genre_scores


def test_postprocess_llm_genre_scores_sorts_scored_items_descending():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="ambient", score=0.41),
            SimpleNamespace(tag="indie rock", score=0.91),
            SimpleNamespace(tag="dream pop", score=0.73),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("indie rock", 0.91),
        ("dream pop", 0.73),
        ("ambient", 0.41),
    ]


def test_postprocess_llm_genre_scores_preserves_input_order_for_items_without_score():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="trip hop", score=None),
            SimpleNamespace(tag="leftfield", score=None),
            SimpleNamespace(tag="post punk", score=None),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("trip hop", None),
        ("leftfield", None),
        ("post punk", None),
    ]


def test_postprocess_llm_genre_scores_places_scored_items_before_unscored_items_deterministically():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="trip hop", score=None),
            SimpleNamespace(tag="ambient", score=0.41),
            SimpleNamespace(tag="leftfield", score=None),
            SimpleNamespace(tag="indie rock", score=0.91),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("indie rock", 0.91),
        ("ambient", 0.41),
        ("trip hop", None),
        ("leftfield", None),
    ]


def test_postprocess_llm_genre_scores_applies_top_n_after_dedupe():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="dream-pop", score=0.95),
            SimpleNamespace(tag=" dream pop ", score=0.91),
            SimpleNamespace(tag="indie rock", score=0.9),
            SimpleNamespace(tag="ambient", score=0.41),
        ],
        top_n=2,
    )

    assert [(item.tag, item.score) for item in result] == [
        ("dream pop", 0.95),
        ("indie rock", 0.9),
    ]


def test_postprocess_llm_genre_scores_drops_weak_scored_items_below_threshold():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="indie rock", score=0.39),
            SimpleNamespace(tag="dream pop", score=0.2),
        ]
    )

    assert result == []


def test_postprocess_llm_genre_scores_keeps_only_strong_items_from_mixed_strong_and_weak():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="indie rock", score=0.91),
            SimpleNamespace(tag="dream pop", score=0.39),
            SimpleNamespace(tag="ambient", score=0.41),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("indie rock", 0.91),
        ("ambient", 0.41),
    ]


def test_postprocess_llm_genre_scores_keeps_items_without_score_through_threshold_phase():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="trip hop", score=None),
            SimpleNamespace(tag="indie rock", score=0.39),
            SimpleNamespace(tag="leftfield", score=None),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("trip hop", None),
        ("leftfield", None),
    ]


def test_postprocess_llm_genre_scores_drops_invalid_non_numeric_or_non_finite_scores():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="indie rock", score="0.91"),
            SimpleNamespace(tag="dream pop", score=float("nan")),
            SimpleNamespace(tag="ambient", score=float("inf")),
            SimpleNamespace(tag="trip hop", score=None),
            SimpleNamespace(tag="leftfield", score=0.65),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("leftfield", 0.65),
        ("trip hop", None),
    ]


def test_postprocess_llm_genre_scores_returns_one_item_for_partial_strong_output():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="space yacht metal", score=0.99),
            SimpleNamespace(tag="indie rock", score=0.9),
            SimpleNamespace(tag="dream pop", score=0.2),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [("indie rock", 0.9)]


def test_postprocess_llm_genre_scores_handles_canonical_unknown_and_weak_mix_predictably():
    result = postprocess_llm_genre_scores(
        [
            SimpleNamespace(tag="dream-pop", score=0.81),
            SimpleNamespace(tag="space yacht metal", score=0.99),
            SimpleNamespace(tag="ambient", score=0.2),
            SimpleNamespace(tag="leftfield", score=None),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [
        ("dream pop", 0.81),
        ("leftfield", None),
    ]
