from app.services.shadow_compare import compare_shadow_tags, normalize_shadow_tags


def test_shadow_compare_both_empty():
    comparison = compare_shadow_tags([], [])

    assert comparison.shared_tags == []
    assert comparison.comparison_signal == "both_empty"


def test_shadow_compare_legacy_only():
    comparison = compare_shadow_tags(["rock"], [])

    assert comparison.legacy_only_tags == ["rock"]
    assert comparison.comparison_signal == "legacy_only"


def test_shadow_compare_llm_only():
    comparison = compare_shadow_tags([], ["rock"])

    assert comparison.llm_only_tags == ["rock"]
    assert comparison.comparison_signal == "llm_only"


def test_shadow_compare_exact_match():
    comparison = compare_shadow_tags(["rock", "alternative"], ["rock", "alternative"])

    assert comparison.shared_tags == ["rock", "alternative"]
    assert comparison.legacy_only_tags == []
    assert comparison.llm_only_tags == []
    assert comparison.shared_tag_count == 2
    assert comparison.comparison_signal == "exact_match"


def test_shadow_compare_top_tag_match_with_weak_partial_overlap():
    comparison = compare_shadow_tags(["rock", "alternative"], ["rock", "indie"])

    assert comparison.top_tag_match is True
    assert comparison.top_tag_mismatch is False
    assert comparison.has_partial_overlap is True
    assert comparison.weak_overlap is True
    assert comparison.comparison_signal == "weak_overlap"


def test_shadow_compare_no_shared_tags():
    comparison = compare_shadow_tags(["rock"], ["jazz"])

    assert comparison.shared_tags == []
    assert comparison.has_no_shared_tags is True
    assert comparison.comparison_signal == "no_shared_tags"


def test_shadow_compare_normalizes_tags_for_diagnostic_comparison():
    comparison = compare_shadow_tags(
        [" Rock ", "Alternative Rock", "rock"],
        ["rock", "alternative   rock"],
    )

    assert normalize_shadow_tags([" Rock ", "Alternative Rock", "rock"]) == [
        "rock",
        "alternative rock",
    ]
    assert comparison.shared_tags == ["rock", "alternative rock"]
    assert comparison.legacy_only_tags == []
    assert comparison.llm_only_tags == []
    assert comparison.comparison_signal == "exact_match"


def test_shadow_compare_top_tag_mismatch_with_full_overlap_but_order_drift():
    comparison = compare_shadow_tags(
        ["rock", "alternative"],
        ["alternative", "rock"],
    )

    assert comparison.top_tag_match is False
    assert comparison.top_tag_mismatch is True
    assert comparison.shared_tag_count == 2
    assert comparison.has_partial_overlap is True
    assert comparison.comparison_signal == "partial_overlap"


def test_shadow_compare_weak_overlap():
    comparison = compare_shadow_tags(
        ["rock", "alternative"],
        ["rock", "electronic"],
    )

    assert comparison.shared_tags == ["rock"]
    assert comparison.weak_overlap is True
    assert comparison.comparison_signal == "weak_overlap"


def test_shadow_compare_deferred_weak_top_partial_diagnostics():
    top_match_comparison = compare_shadow_tags(
        ["rock", "alternative"],
        ["rock", "electronic"],
    )
    top_mismatch_comparison = compare_shadow_tags(
        ["rock", "alternative"],
        ["alternative", "electronic"],
    )

    assert top_match_comparison.top_tag_match is True
    assert top_match_comparison.weak_overlap is True
    assert top_mismatch_comparison.top_tag_mismatch is True
    assert top_mismatch_comparison.weak_overlap is True


def test_shadow_compare_deferred_no_shared_tags_boundary_diagnostics():
    comparison = compare_shadow_tags(
        ["shoegaze", "dream pop"],
        ["drum and bass", "breakbeat"],
    )

    assert comparison.has_no_shared_tags is True
    assert comparison.legacy_only_tags == ["shoegaze", "dream pop"]
    assert comparison.llm_only_tags == ["drum and bass", "breakbeat"]
    assert comparison.comparison_signal == "no_shared_tags"


def test_shadow_comparison_can_be_rendered_as_dict():
    comparison = compare_shadow_tags(["rock"], ["rock"])

    assert comparison.to_dict() == {
        "shared_tags": ["rock"],
        "legacy_only_tags": [],
        "llm_only_tags": [],
        "shared_tag_count": 1,
        "legacy_tag_count": 1,
        "llm_tag_count": 1,
        "top_tag_match": True,
        "top_tag_mismatch": False,
        "has_no_shared_tags": False,
        "has_partial_overlap": False,
        "weak_overlap": False,
        "comparison_signal": "exact_match",
    }
