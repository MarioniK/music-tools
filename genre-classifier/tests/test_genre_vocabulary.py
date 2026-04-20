from types import SimpleNamespace

from app.genres.normalization import canonicalize_genre_scores, normalize_genre_label


def test_normalize_genre_label_trims_and_canonicalizes_dream_pop():
    assert normalize_genre_label(" Dream Pop ") == "dream pop"


def test_normalize_genre_label_collapses_dream_pop_aliases():
    assert normalize_genre_label("dream-pop") == "dream pop"
    assert normalize_genre_label("dream pop") == "dream pop"


def test_canonicalize_genre_scores_dedupes_after_alias_normalization():
    result = canonicalize_genre_scores(
        [
            SimpleNamespace(tag="dream-pop", score=0.4),
            SimpleNamespace(tag=" dream pop ", score=0.8),
            SimpleNamespace(tag="Dream Pop", score=0.6),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [("dream pop", 0.8)]


def test_normalize_genre_label_drops_out_of_vocabulary_values():
    assert normalize_genre_label("space yacht metal") is None


def test_canonicalize_genre_scores_returns_empty_when_all_items_are_out_of_vocabulary():
    result = canonicalize_genre_scores(
        [
            SimpleNamespace(tag="space yacht metal", score=0.8),
            SimpleNamespace(tag="cosmic whalewave", score=0.7),
        ]
    )

    assert result == []


def test_canonicalize_genre_scores_prefers_numeric_score_over_none_for_same_canonical_tag():
    result = canonicalize_genre_scores(
        [
            SimpleNamespace(tag="dream-pop", score=None),
            SimpleNamespace(tag="dream pop", score=0.7),
        ]
    )

    assert [(item.tag, item.score) for item in result] == [("dream pop", 0.7)]
