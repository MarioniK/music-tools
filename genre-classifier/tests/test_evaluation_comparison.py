from app.evaluation import compare_provider_results, extract_canonical_tag_sequence
from app.providers.base import ProviderGenreScore, ProviderResult
from app.providers.schema import ValidatedGenreItem, ValidatedProviderResult


def test_extract_canonical_tag_sequence_normalizes_and_deduplicates_tags():
    result = ProviderResult(
        genres=[
            ProviderGenreScore(tag=" Dream-Pop ", score=0.7),
            ProviderGenreScore(tag="dream_pop", score=0.9),
            ProviderGenreScore(tag="left field", score=0.5),
        ],
        provider_name="stub",
        model_name=None,
    )

    assert extract_canonical_tag_sequence(result) == [
        "dream pop",
        "left field",
    ]


def test_compare_provider_results_builds_overlap_and_ranking_drift_summary():
    legacy_result = ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="indie rock", score=0.91),
            ValidatedGenreItem(tag="dream pop", score=0.73),
            ValidatedGenreItem(tag="ambient", score=0.41),
        ],
        provider_name="legacy_musicnn",
        model_name="legacy-v1",
        total_items_received=3,
        total_items_kept=3,
        dropped_items_count=0,
    )
    llm_result = ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="dream pop", score=0.88),
            ValidatedGenreItem(tag="ambient", score=0.61),
            ValidatedGenreItem(tag="trip hop", score=0.52),
        ],
        provider_name="llm",
        model_name="llm-v1",
        total_items_received=3,
        total_items_kept=3,
        dropped_items_count=0,
    )

    summary = compare_provider_results(legacy_result, llm_result)

    assert summary["legacy_tags"] == ["indie rock", "dream pop", "ambient"]
    assert summary["llm_tags"] == ["dream pop", "ambient", "trip hop"]
    assert summary["shared_tags"] == ["dream pop", "ambient"]
    assert summary["legacy_only_tags"] == ["indie rock"]
    assert summary["llm_only_tags"] == ["trip hop"]
    assert summary["overlap_summary"] == {
        "legacy_tag_count": 3,
        "llm_tag_count": 3,
        "shared_tag_count": 2,
        "legacy_only_tag_count": 1,
        "llm_only_tag_count": 1,
        "overlap_ratio_vs_legacy": 2 / 3,
        "overlap_ratio_vs_llm": 2 / 3,
        "jaccard_similarity": 0.5,
    }
    assert summary["ranking_drift"] == [
        {
            "tag": "dream pop",
            "legacy_rank": 2,
            "llm_rank": 1,
            "rank_delta": -1,
            "absolute_rank_delta": 1,
        },
        {
            "tag": "ambient",
            "legacy_rank": 3,
            "llm_rank": 2,
            "rank_delta": -1,
            "absolute_rank_delta": 1,
        },
    ]
    assert summary["warning_cases"] == []


def test_compare_provider_results_flags_empty_output_and_no_shared_tags():
    legacy_result = ValidatedProviderResult(
        genres=[
            ValidatedGenreItem(tag="indie rock", score=0.91),
        ],
        provider_name="legacy_musicnn",
        model_name=None,
        total_items_received=1,
        total_items_kept=1,
        dropped_items_count=0,
    )
    llm_result = {
        "genres": [],
        "provider_name": "llm",
        "model_name": "llm-empty",
    }

    summary = compare_provider_results(legacy_result, llm_result)

    assert summary["llm_tags"] == []
    assert summary["warning_flags"]["llm_empty_output"] is True
    assert summary["warning_flags"]["no_shared_tags"] is False
    assert summary["warning_cases"] == ["llm_empty_output"]


def test_compare_provider_results_flags_weak_and_partial_llm_output():
    legacy_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="indie rock", score=0.91),
            ProviderGenreScore(tag="dream pop", score=0.73),
            ProviderGenreScore(tag="ambient", score=0.61),
        ],
        provider_name="legacy_musicnn",
        model_name=None,
    )
    llm_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag="dream pop", score=0.2),
        ],
        provider_name="llm",
        model_name=None,
    )

    summary = compare_provider_results(legacy_result, llm_result)

    assert summary["shared_tags"] == ["dream pop"]
    assert "legacy_weak_top_score" not in summary["warning_flags"]
    assert summary["warning_flags"]["llm_partial_output"] is True
    assert summary["warning_flags"]["llm_weak_top_score"] is True
    assert summary["warning_cases"] == [
        "llm_partial_output",
        "llm_weak_top_score",
    ]
